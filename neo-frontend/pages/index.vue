<template>
  <div class="flex flex-col items-center justify-end h-screen">
    <div
      class="p-4  text-center"
    >
    <UAlert
      :color="statusConfig.color"
      :title="statusConfig.title"
      :description="listening ? `${assistantName} is listening` : ''"
    />
    </div>

    <div
      class="mt-auto mb-auto font-thin flex flex-col items-center justify-center text-center gap-2 bg-gray-750 rounded-md max-w-3/4"
    >
      <p
        v-show="!gettingResponse"
        class="max-w-3/4 max-h-[50vh] text-xl break-words"
      >
        {{ response }}
      </p>
    </div>
    <div>
      <SettingsPanel class="absolute right-4 top-4" />
    </div>
    <p v-show="loadingPercent < 100 && ttsEngine !== 'server'" class="animate-pulse">{{ assistantName }} is loading...</p>
    <UProgress v-show="loadingPercent != 100 && ttsEngine !== 'server'" v-model="loadingPercent" color="neutral" class="max-w-lg w-lg" />
    <UProgress v-show="gettingResponse" class="w-lg" />
    <UTextarea
      class="w-1/2 m-8 "
      color="neutral"
      variant="subtle"
      placeholder="Type something..."
      :maxrows="8"
      autoresize
      v-model="value"
      :disabled="connectionStatus !== serverStatus.CONNECTED"
      @keydown.enter="(event: KeyboardEvent) => { if (!event.shiftKey) handleEnter(event) }"
    />
  </div>
</template>

<script setup lang="ts">
import SettingsPanel from '~/components/SettingsPanel.vue';
import * as tts from '@diffusionstudio/vits-web';
const {
  llm,
  ttsEngine,
  ttsVoice,
  ttsSpeed,
  assistantName,
  callNameInterval,
  micMuted,
  speakerMuted
} = useConfig();

const { MicVAD, utils } = await import("@ricky0123/vad-web");
const enum serverStatus {
  CONNECTING = "Connecting",
  CONNECTED = "Connected",
  REFUSED = "Connection Refused",
  ERROR = "Error Connecting",
}
const statusConfig = computed<{
  color: "neutral" | "primary" | "error" | "secondary" | "success" | "info" | "warning" | undefined;
  title: string;
  icon: string;
}>(() => {
  switch (connectionStatus.value) {
    case serverStatus.CONNECTING:
      return {
        color: 'neutral',
        title: 'Connecting...',
        icon: 'svg-spinners:8-dots-rotate',
      }
    case serverStatus.CONNECTED:
      return {
        color: 'primary',
        title: 'Connected!',
        icon: 'material-symbols-light:stat-0-rounded',
      }
    case serverStatus.REFUSED:
      return {
        color: 'error',
        title: 'Connection Refused',
        icon: 'material-symbols-light:warning',
      }
    case serverStatus.ERROR:
      return {
        color: 'error',
        title: 'Connection Error',
        icon: 'material-symbols-light:warning',
      }
    default:
      return {
        color: 'neutral',
        title: 'Status Unknown',
        icon: 'i-lucide-terminal',
      }
  }
})

const value = ref("");
const connectionStatus = ref(serverStatus.CONNECTING);
const gettingResponse = ref(false);
const history = ref([]);
const response = ref("");
const currentAudioBlob = ref<Blob | null>(null);
const listening = ref(false);
const currentCallNameSeconds = ref(0);
const loadingPercent = ref(0);
let interval: ReturnType<typeof setInterval> | null = null;
let myvad: any = null;

onMounted(() => {
  handleConnect();
  listening.value = !(micMuted.value);
});

async function startMicVAD() {
  try {
    myvad = await MicVAD.new({
      onSpeechEnd: (audio) => {
        console.log("Speech Ended");
        console.log(audio);
        const wavBuffer = utils.encodeWAV(audio);
        const audioBlob = new Blob([wavBuffer], { type: "audio/wav" });
        currentAudioBlob.value = audioBlob;
      },
      positiveSpeechThreshold: 0.7,
    });
    myvad.start();
    listening.value = true;
  } catch (error: any) {
    console.error(error);
  }
}

async function downloadTTSEngine() {
  try {
    if (tts.stored.length > 0) {
      console.log("TTS engine already downloaded:", tts.stored);
      return;
    }
    await tts.download('en_US-hfc_female-medium', (progress) => {
      console.log(`Downloading ${progress.url} - ${Math.round(progress.loaded * 100 / progress.total)}%`);
      loadingPercent.value = Math.round(progress.loaded * 100 / progress.total);
      if (loadingPercent.value === 100) {
        console.log("TTS model downloaded successfully.");
      }
    });
  } catch (error: any) {
    console.error("Error downloading TTS engine:", error);
  }
}

onMounted(async () => {
  // Only run this code in the browser
  if (process.client || typeof window !== "undefined") {
    try {
      if (!micMuted) {
        await startMicVAD();
      }
    } catch (error: any) {
      console.error(error);
    }
  }

  if (ttsEngine.value === "local") {
    // Initialize the TTS engine
    await downloadTTSEngine();
  }
});

// When we get a new audio blob, submit it to the server
watch(currentAudioBlob, (newValue, oldValue) => {
  if (listening.value == true) {
    submitAudio(newValue);
  }
});

watch(micMuted, async (newVal, oldVal) => {
  // If the mic is muted, destroy the VAD instance
  if (myvad) {
    if (newVal == true) {
      myvad.destroy();
      listening.value = false;
    } else {
      await startMicVAD();
    }
  } else {
    if (newVal == false) {
      await startMicVAD();
    }
  }
});

watch(ttsEngine, async (newVal, oldVal) => {
  if (newVal === "local" && tts.stored.length === 0) {
    // Initialize the TTS engine
    await downloadTTSEngine();
  }
});

function setCallNameInterval(seconds: number = callNameInterval.value) {
    if (interval) { clearInterval(interval); }

    currentCallNameSeconds.value = seconds;
    interval = setInterval(() => {
      if (currentCallNameSeconds.value > 0) {
        currentCallNameSeconds.value--;
        console.log(`Call name interval: ${currentCallNameSeconds.value} seconds remaining`);
      } else {
        if (interval) { clearInterval(interval); }
        interval = null;
      }
    }, 1000);
  }

// Submit audio to server, get transcription, and send query to server
async function submitAudio(audioBlob: Blob | null) {
  if (connectionStatus.value !== serverStatus.CONNECTED) {
    console.error("Not connected to the server");
    return;
  }
  listening.value = false; // Stop listening while processing audio
  gettingResponse.value = true; // Show loading state
  const formData = new FormData();
  if (audioBlob) {
    formData.append("file", audioBlob, "audio.wav");
  } else {
    console.error("No audio blob available to submit.");
    return;
  }
  formData.append("model", "Systran/faster-whisper-tiny.en");

  const res = await fetch("http://localhost:8000/v1/audio/transcriptions", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Transcription failed");
  }
  const data = await res.json();
  const transcription = data.text;

  console.log("Transcription:", transcription);

  // If the call name interval is 0, the user needs to call the assistant's name again
  if ((callNameInterval.value == 0 && !transcription.toLowerCase().includes(assistantName.value.toLowerCase())) || transcription.length < 1) {
    listening.value = true; // Reset listening state
    return;
  }
  // Send the query to the server
  try {
    const res = await sendQuery(transcription);
    if (!res) {
      listening.value = true; // Reset listening state if no response
      return;
    }
    response.value = res.response.LLM_response;
  } catch (error) {
    listening.value = true; // Reset listening state if there's an error
    response.value = `${assistantName} is malfunctioning.`;
  }
  gettingResponse.value = false;
}

// Check connection to the server
async function handleConnect() {
  try {
    const response = await fetch("http://127.0.0.1:5000/health", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    const data = await response.json();
    if (data.status === "healthy") {
      connectionStatus.value = serverStatus.CONNECTED;
    } else {
      connectionStatus.value = serverStatus.REFUSED;
    }
  } catch (error) {
    connectionStatus.value = serverStatus.ERROR;
  }
}

// Send query to the server and update history
async function sendQuery(query: string) {
  try {
    if (!query || query.trim() === "" || connectionStatus.value !== serverStatus.CONNECTED) {
      return;
    }

    // Stop listening while sending query and speaking response to avoid feedback loops
    listening.value = false;

    // Send query and history to the server
    const response = await fetch("http://127.0.0.1:5000/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: query, history: history.value }),
    });
    const res = await response.json();

    // Add result of query to history
    history.value = res.response.history.slice(
      Math.max(res.response.history.length - 10, 0),
      res.response.history.length
    );

    // If the speaker isn't muted, play the audio
    if (!speakerMuted.value) {
      let wav: string | null = null;
      // Play the response using TTS
      if (ttsEngine.value === "local") {
        let blob: Blob;
        blob = await tts.predict({
          text: res.response.LLM_response,
          voiceId: 'en_US-hfc_female-medium',
        });
        wav = URL.createObjectURL(blob)
      } else {
        // Use the TTS server to get the audio file
        wav = await getSpeechFileFromTTSServer(res.response.LLM_response);
      }

      try {
        // Play the audio
        const audio = new Audio();
        audio.src = wav;
        audio.playbackRate = ttsSpeed.value;
        audio.play();
        audio.onended = () => {
          listening.value = true;
          setCallNameInterval(callNameInterval.value); // Reset the timer
        };
      } catch (error) {
        console.error("Error playing audio:", error);
        listening.value = true; // Reset listening state if audio fails
      }
    } else {
      listening.value = true;
      setCallNameInterval(callNameInterval.value); // Reset the timer
      }
    return res;
  } catch (error) {
    console.error("Error submitting data:", error);
  }
}

// Handle text input submission
async function handleEnter(event: KeyboardEvent) {
  // Prevent default behavior
  event.preventDefault();

  if (!value.value.trim()) {
    // If the input is empty, do nothing
    return;
  }
  const query = value.value;
  // Clear the input
  value.value = "";

  // Set gettingResponse to true to show the loading state
  gettingResponse.value = true;
  // Send the query to the server
  try {
    const res = await sendQuery(query);
    if (!res) {
      return;
    }
    response.value = res.response.LLM_response;
  } catch (error) {
    response.value = `${assistantName} is malfunctioning.`;
  }

  gettingResponse.value = false;
}

// Get speech file from TTS server
async function getSpeechFileFromTTSServer(text: string) {
  const params = new URLSearchParams({ text });

  const response = await fetch(`http://localhost:5008/?${params.toString()}`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Server error: ${response.status}`);
  }

  const blob = await response.blob(); // WAV file
  const url = URL.createObjectURL(blob);
  return url;
}
</script>
