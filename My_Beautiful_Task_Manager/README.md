# **My Beautiful Task Manager**

A visually appealing and user-friendly **task management application** built with Python and PyQt6. It helps you organize tasks, manage priorities, deadlines, and even attach images to your tasks or planner. With support for custom themes, drag-and-drop functionality, and a clean interface, it is perfect for users who value aesthetics and functionality in their task managers.

---

## **Key Features**

### 📝 **Task Management**
- Add, edit, and delete tasks.
- Track tasks with priority levels: **Low**, **Medium**, **High**.
- Manage task statuses: **To Do**, **In Progress**, **Completed**.
- Add detailed descriptions and due dates for each task.
- Save and load tasks to/from a JSON file.

### 📸 **Image Management**
- Attach images to tasks from your local storage or via URL.
- View task images in full size within the application.
- Manage a planner image gallery to personalize your workspace.

### 🎨 **Themes**
- Choose from 10 beautiful themes, including **Pastel Pink**, **Ocean Blue**, **Lavender**, and more.
- Seamlessly switch between themes to customize the application's look and feel.

### 🖼 **Drag-and-Drop Support**
- Drag and drop images directly into the planner image gallery.

### 🛠 **Additional Features**
- **Interactive Toolbar**: Quickly add new tasks or delete existing ones.
- **Instructions Panel**: Integrated help guide to understand how the app works.
- **Resizable Gallery**: Manage planner and task images with a convenient scrollable gallery.
- **Save and Load Planner Settings**: Easily save all your tasks and planner settings and load them later.

---

## **How to Use**

### 📥 **Adding a New Task**
1. Click the **New Task** icon on the toolbar.
2. Fill out the task details (title, description, due date, priority, status).
3. Attach images if necessary.
4. Save your task using the **Save Task** button.

### 🗑 **Deleting a Task**
1. Select a task from the **Task List**.
2. Click the **Delete Task** icon or use the right-click menu.

### 📸 **Adding Images**
- **To a Task**:
  - Select the task and use the **Add Image from Disk** or **Add Image from URL** buttons.
- **To the Planner**:
  - Use the **Add Image to Planner** button or drag and drop images into the app.

### 🖼 **Viewing Images**
- Click on any image thumbnail to view it in full size.

### 🎨 **Changing Themes**
- Use the **Theme Dropdown** in the toolbar to switch between themes instantly.

### 📄 **Saving and Loading Tasks**
- Save your current tasks and planner settings to a JSON file using the **Save** option in the File menu.
- Reload tasks and planner settings from a saved JSON file using the **Load** option.

---

## **Requirements**
- Python 3.9 or later.
- **PyQt6**: Install using `pip install PyQt6`.
- **Requests**: Install using `pip install requests`.

---

## **Installation**

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/task-manager.git
   cd task-manager
