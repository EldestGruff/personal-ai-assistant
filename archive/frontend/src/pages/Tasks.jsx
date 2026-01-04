import React, { useState, useEffect } from 'react';

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/tasks', {
          headers: {
            'X-API-Key': 'D2E1B06E-2C3D-4245-B271-CAA054DEDCE4',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (Array.isArray(data.data)) {
          setTasks(data.data);
        } else {
          console.error('API response is not an array:', data);
          setError('Failed to load tasks. The API returned an unexpected response.');
        }
      } catch (error) {
        console.error('Error fetching tasks:', error);
        setError(`Error fetching tasks: ${error.message}`);
      }
    };

    fetchTasks();
  }, []);

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!newTask.trim()) return;

    try {
      const response = await fetch('http://localhost:8000/api/v1/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'D2E1B06E-2C3D-4245-B271-CAA054DEDCE4',
        },
        body: JSON.stringify({ description: newTask }),
      });

      if (response.ok) {
        const newTaskData = await response.json();
        setTasks([...tasks, newTaskData.data]);
        setNewTask('');
      } else {
        console.error('Error adding task:', response.statusText);
        setError(`Error adding task: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error adding task:', error);
      setError(`Error adding task: ${error.message}`);
    }
  };

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  return (
    <div>
      <h1>Tasks</h1>
      <form onSubmit={handleAddTask} className="mb-4">
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            placeholder="Enter a new task"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
          />
          <button className="btn btn-primary" type="submit">
            Add Task
          </button>
        </div>
      </form>
      <ul className="list-group">
        {tasks.map((task) => (
          <li key={task.id} className="list-group-item">
            {task.description}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Tasks;
