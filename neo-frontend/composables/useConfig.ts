// composables/useConfig.ts

import { ref } from 'vue'

const llm = ref('claude')
const ttsEngine = ref('server')
const ttsVoice = ref('jarvis')
const ttsSpeed = ref(1.10)
const assistantName = ref('Jarvis')
const callNameInterval = ref(15)
const micMuted = ref(true)
const speakerMuted = ref(false)

export const useConfig = () => {
    return {
        llm,
        ttsEngine,
        ttsVoice,
        ttsSpeed,
        assistantName,
        callNameInterval,
        micMuted,
        speakerMuted
    }
}