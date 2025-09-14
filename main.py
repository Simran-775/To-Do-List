from datetime import datetime
from colorama import Fore,Style,init
from collections import Counter
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import sys

client = MongoClient("mongodb://localhost:27017/to_do_db")
db = client.to_do_db
task_collection = db.tasks


print("hello")
init(autoreset=True)
class TaskManager:
    def __init__(self):
        self.task = {}

    # ---------- Utility Methods ----------

    def print_task(self, task):
        color_map = {
        "High": Fore.RED,
        "Medium": Fore.YELLOW,
        "Low": Fore.GREEN
        }
        color = color_map.get(task["priority"], Fore.WHITE)
        due = datetime.strptime(task["due_date"], "%d-%m-%Y")
        today = datetime.today()
        if due<today:
            colors = Fore.RED
            status = "Overdue"
        else:
            colors = Fore.WHITE
            status = ""
        
        print("*********************************")
        print(f"ID: {task.get('_id')}")
        print(f"Title: {task.get('title')}")
        print(f"Description: {task.get('desc')}")
        print(f"Due Date: {task.get('due_date')} {colors}{status}{Style.RESET_ALL}")
        print(f"Priority: {color}{task.get('priority')}{Style.RESET_ALL}")
        print("Subtasks :-")
        if task["sub-tasks"]:
            for i, st in enumerate(task["sub-tasks"], start=1):
                status = "✔" if st["done"] else "✘"
                print(f"  {i}. [{status}] {st['title']}")
        else:
            print("No subtasks")
        if task["tag"] != "":
            print(f"Tag: {task['tag']}")

        print(f"Status: {task.get('status')}")
        print(f"Created At: {task.get('date-created')}")
        print("*********************************")

    def sort_task_by_priority(self, tasks):
        priority_order = {"High": 1, "Medium": 2, "Low": 3}
        return sorted(tasks, key=lambda x: priority_order.get(x["priority"], 4))


    # ---------- CRUD Methods ----------
    def create_task(self):
        title = input("Enter title: ").strip().capitalize()
        desc = input("Enter Description: ").strip()
        while True:
            due_date = input("Enter Due Date (DD-MM-YYYY): ").strip()
            try:
                datetime.strptime(due_date, "%d-%m-%Y")
                break
            except ValueError:
                print("Invalid date format. Please use DD-MM-YYYY.")

        while True:
            priority = input("Enter priority (High/Medium/Low): ").capitalize()
            if priority in ["High", "Medium", "Low"]:
                break
            print("Invalid priority. Please enter High, Medium, or Low.")
        subtasks = []
        while True:
            flag = input("Do you want to add subtask (Y/N)? ").lower()
            if flag in ['y','n']:
                if flag == 'y':
                    subtitle = input("Enter Tilte: ")
                    subtasks.append({"title":subtitle,"done":False})
                else:
                    break
            else:
                print("Invalid Choice")

        isTag = input("Do u want to add Tags (Y/N)?").lower()
        if isTag in ["y","n"]:
            if isTag == "y":
                tag = input("Enter the Tag name: ").capitalize()
            else:
                tag = ""
        else:
            print("Invalid choice")

        self.task = {
            'title': title,
            'desc': desc,
            'due_date': due_date,
            'priority': priority,
            'date-created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'sub-tasks': subtasks,
            'tag' : tag,
            'status': "Pending"
        }
        task_collection.insert_one(self.task)
        print("Task Created Successfully ✅")

    def view_tasks(self):
        tasks = list(task_collection.find())
        if not tasks:
            print("No tasks found.")
            return
        for task in tasks:
            due = datetime.strptime(task["due_date"], "%d-%m-%Y")
            if due < datetime.today() and task["status"] != "Completed":
                task_collection.update_one({"_id":task["_id"]},{"$set":{"status":"Overdue"}})
            self.print_task(task)

        

    def get_task(self):
        try:
            keyword = ObjectId(input("Enter the ID of the task: "))
        except ValueError:
            print("Invalid ID.")
            return
        task = task_collection.find_one({"_id":keyword})
        self.print_task(task)

    def search_task(self):
        keyword = input("Enter the keyword of either title or description or subtask or Tag: ").lower()

        result = task_collection.find({
            "$or": [
                { "title":    { "$regex": keyword, "$options": "i" } },
                { "desc":     { "$regex": keyword, "$options": "i" } },
                { "sub-tasks.title": { "$regex": keyword, "$options": "i" } },
                { "tag":      { "$regex": keyword, "$options": "i" } }
            ]
        })

        results = list(result)
        for task in results:
            self.print_task(task)


    def filter(self):
        print("Select your Filter")
        print(
            """
        ##########################
            Select your Filter
        1. Priority
        2. Status
        3. Tag (Category)
        ##########################
        """
        )
        while True:
            try:
                choice = int(input("Enter choice: "))
                if choice not in [1,2,3]:
                    raise ValueError
                break
            except ValueError:
                print("Invalid Choice. Enter a number between 1-3.")
        if choice == 1:
            priority =  input("Enter the priority: (High/Low/Medium)").capitalize()
            tasks = list(task_collection.find({"priority":priority}))
        elif choice == 2:
            status =  input("Enter the status: (Pending/Completed/Overdue)").capitalize()
            tasks = list(task_collection.find({"status":status}))
        elif choice == 3:
            key = input("Enter the tag/category: ").capitalize()
            tasks = list(task_collection.find({"tag":key}))
        for task in tasks:
            self.print_task(task)
                

    def sorting_task(self):
        choice = input("Enter the sorting criteria (Priority/Due Date/Date Created)").lower()
        if choice in ["priority","due date","date created"]:
            if choice == "priority":
                tasks = list(task_collection.find())  # fetch all
                tasks = self.sort_task_by_priority(tasks)  # custom sort
            if choice == "due date":
                tasks = list(task_collection.find().sort("due_date", 1))

            if choice == "date created":
                tasks = list(task_collection.find().sort("date-created", 1))

            for task in tasks:
                self.print_task(task)
        else:
            print("Invalid Option")

        
    def del_tasks(self):
        try:
            keyword = ObjectId(input("Enter ID of task you want to delete: "))
            print(keyword)   
        except ValueError:
            print("Invalid ID.")
            return
        do = task_collection.delete_one({"_id":keyword})


    def update_task(self):
        print("These are the Tasks in your Memo. Please select the one you want to update")
        tasks = list(task_collection.find())
        length = len(tasks)
        ids = []
        for i,task in enumerate(tasks,start=1):
            print(f" {i} {task["title"]}")
            ids.append(task["_id"])

        while True:
            ch = int(input("Enter your choice: "))
            if ch not in range(1,length+1):
                print("Invalid choice")
            else:
                break
        id = ids[ch-1]
        
        attributes = ["title","desc","due_date","priority","sub-tasks","tag","status"]
        print("Which attribute do you want to update?")
        print(
            """
        ##########################
            Select your Attribute (1-7)
        1. Title
        2. Description
        3. Due date
        4. Priority
        5. Sub-Tasks
        6. Tag
        7. Status
        ##########################
        """
        )
        ind = int(input("Enter choice: "))
        while True:
            if ind not in range(1,8):
                print("Invalid choice.")
            else:
                break
        attr = attributes[ind-1]
        print(f"Updating {attr}")
        if attr == "sub-tasks":
            sub_tasks = list(task_collection.find({"_id": id}, {"sub-tasks": 1, "_id": 0}))[0]["sub-tasks"]

            keyword = input("Enter subtask keyword to update: ").strip().lower()
            for sub_task in sub_tasks:
                if keyword in sub_task["title"].lower():
                    title = sub_task["title"]
                    print(" ## Sub-task found ")
                    print(f"Title : {title}")
                    print(f"Done : {sub_task['done']}")

                    att = input("Enter what you want to update (Title/Done): ").strip().lower()

                    if att == "title":
                        val = input("Enter new title for sub-task: ").strip()
                        task_collection.update_one(
                            {"_id": id, "sub-tasks.title": title},   # use correct field name
                            {"$set": {"sub-tasks.$.title": val}}
                        )

                    elif att == "done":
                        val = input(f"Enter new val for {att} (True/Yes/Y): ").strip().lower()
                        done_val = True if val in ["true", "yes", "y", "1"] else False

                        task_collection.update_one(
                            {"_id": id, "sub-tasks.title": title},   # correct field name
                            {"$set": {"sub-tasks.$.done": done_val}}
                        )
                    sub_tasks = list(task_collection.find({"_id": id}, {"sub-tasks": 1, "_id": 0}))[0]["sub-tasks"]
                    subtask_count = len(sub_tasks)
                    done_count = 0
                    print("✅ Sub-task updated successfully.")
                    break
                
            else:
                print("No such sub-task found")
            

            for sub_task in sub_tasks:
                if sub_task["done"] == True:
                    done_count += 1
            if subtask_count == done_count:
                task_collection.update_one({"_id":id},{"$set":{"status":"Completed"}})
                print("All subtasks completed, status also updated successfully")

            
        else:
            if attr == "due_date":
                while True:
                    try:
                        val = input(f"Enter new value for {attr} (DD-MM-YYYY): ").strip()
                        datetime.strptime(val, "%d-%m-%Y")
                        break
                    except ValueError:
                        print("Invalid date format. Use DD-MM-YYYY.")
            elif attr == "priority":
                while True:
                        val = input(f"Enter new value for {attr} (High/Medium/Low) ").strip().capitalize()
                        if val not in ["High", "Medium", "Low"]:
                            print("Invalid priority.")
                        else:
                            break
            elif attr == "status":
                while True:
                        val = input(f"Enter new value for {attr} (Pending/Completed/Overdue) ").strip().capitalize()
                        if val not in ["Pending", "Completed", "Overdue"]:
                            print("Invalid status.")
                        else:
                            break
            else:
                val = input(f"Enter new value for {attr} :").strip()
            task_collection.update_one({"_id":id},{"$set":{attr:val}})
        print("Task Updated Successfully")

    def show_dashboard(self):
        total = len(list(task_collection.find()))
        today = datetime.today().date()
        completed = len(list(task_collection.find({"status":"Completed"})))
        pending = len(list(task_collection.find({"status":"Pending"})))
        overdue = len(list(task_collection.find({"status":"Overdue"})))
        high = len(list(task_collection.find({"priority":"High"})))
        med = len(list(task_collection.find({"priority":"Medium"})))
        low = len(list(task_collection.find({"priority":"Low"})))
        print("\n📊 Dashboard Statistics")
        print("=" * 30)
        print(f"Total Tasks     : {total}")
        print(f"Completed       : {completed}")
        print(f"Pending         : {pending}")
        print(f"Overdue         : {overdue}")
        print("\nPriority Breakdown:")
        print(f"  High : {high}")
        print(f"  Medium : {med}")
        print(f"  Low : {low}")
        
        print("=" * 30 + "\n")



    def exit(self):
        print("Exiting... Bye 👋")
        sys.exit()


# ---------- Main Menu ----------
def main():
    

    task = TaskManager()
    while True:
        print(
            """
        ######################
            TO-DO App Menu
        ######################
            1. Add New Task
            2. View All Tasks
            3. view task by id
            4. Search Tasks By Title or Description
            5. Update Task
            6. Delete Task
            7. Filter Task
            8. Sort Tasks
            9. Show Dashboard
            10. Exit
        ######################
            """
        )
        while True:
            try:
                choice = int(input("Enter your Choice: "))
                if choice not in range(1,12):
                    raise ValueError
                break
            except ValueError:
                print("Invalid Input. Enter a number between 1-11.")

        match choice:
            case 1: task.create_task()
            case 2: task.view_tasks()
            case 3: task.get_task()
            case 4: task.search_task()
            case 5: task.update_task()
            case 6: task.del_tasks()
            case 7: task.filter()
            case 8: task.sorting_task()
            case 9: task.show_dashboard()
            case 10: return


if __name__ == "__main__":
    main()

    
