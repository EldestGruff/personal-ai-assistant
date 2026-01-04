import React, { useState, useEffect } from 'react';

const Thoughts = () => {
  const [thoughts, setThoughts] = useState([]);
  const [newThought, setNewThought] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchThoughts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/thoughts', {
          headers: {
            'X-API-Key': 'D2E1B06E-2C3D-4245-B271-CAA054DEDCE4',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (Array.isArray(data.data)) {
          setThoughts(data.data);
        } else {
          console.error('API response is not an array:', data);
          setError('Failed to load thoughts. The API returned an unexpected response.');
        }
      } catch (error) {
        console.error('Error fetching thoughts:', error);
        setError(`Error fetching thoughts: ${error.message}`);
      }
    };

    fetchThoughts();
  }, []);

  const handleAddThought = async (e) => {
    e.preventDefault();
    if (!newThought.trim()) return;

    try {
      const response = await fetch('http://localhost:8000/api/v1/thoughts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'D2E1B06E-2C3D-4245-B271-CAA054DEDCE4',
        },
        body: JSON.stringify({ message: newThought }),
      });

      if (response.ok) {
        const newThoughtData = await response.json();
        setThoughts([...thoughts, newThoughtData.data]);
        setNewThought('');
      } else {
        console.error('Error adding thought:', response.statusText);
        setError(`Error adding thought: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error adding thought:', error);
      setError(`Error adding thought: ${error.message}`);
    }
  };

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  return (
    <div>
      <h1>Thoughts</h1>
      <form onSubmit={handleAddThought} className="mb-4">
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            placeholder="Enter a new thought"
            value={newThought}
            onChange={(e) => setNewThought(e.target.value)}
          />
          <button className="btn btn-primary" type="submit">
            Add Thought
          </button>
        </div>
      </form>
      <ul className="list-group">
        {thoughts.map((thought) => (
          <li key={thought.id} className="list-group-item">
            {thought.message}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Thoughts;
