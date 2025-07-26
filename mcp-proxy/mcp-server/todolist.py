import os

class TodoList:
    def __init__(self, dir, filename):
        folder_path = os.path.expanduser(dir)
        self.filepath = os.path.join(folder_path, filename)
        self.todo_set = set()
        self.initialize_list()

    def add_task(self, task):
        self.todo_set.add(str(task))
        self.write_to_file()
        self.initialize_list()

    def initialize_list(self):
        try:
            with open(self.filepath, "a+") as file:
                file.seek(0)
                todo_list = [line for line in file.read().strip().split("\n") if line]
            self.todo_set = set(todo_list)
        except FileNotFoundError:
            self.todo_set = set()

    def remove_task(self, task):
        if task in self.todo_set:
            self.todo_set.remove(task)
            self.write_to_file()
            self.initialize_list()
        else:
            raise Exception(f"task not found: {task}")

    def write_to_file(self):
        with open(self.filepath, "w") as file:
            file.write("\n".join(sorted(self.todo_set)))

    def get_todo_list(self):
        return sorted(self.todo_set)