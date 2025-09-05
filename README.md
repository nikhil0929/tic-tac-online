# Tic-Tac-Toe Online

A simple Tic-Tac-Toe game built with FastAPI and React (not really needed but its there)

<img width="970" height="991" alt="image" src="https://github.com/user-attachments/assets/d7f369c9-e484-4bd5-9ace-e49aa912e948" />

# Start the application

1. Clone the repository

   ```
   git clone https://github.com/nikhil0929/tic-tac-online.git
   ```

2. Navigate to the project directory:

   ```
   cd tic-tac-online
   ```

3. Create and activate the environment:

   ```
   conda create -n tic-tac-online python=3.10
   conda activate tic-tac-online
   pip install -r requirements.txt
   ```

4. Start new Database:

   ```
   docker run -d --name tic-tac-online -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=tic_tac_online -p 8766:5432 postgres:latest
   ```

5. Install and start Redis (macOS):

   ```
   brew install redis
   brew services start redis
   ```

6. (Optional) Connect to it on Postico (or any other PostgreSQL client) so you can see the database:

   ```
   postgres://postgres:postgres@localhost:8766/tic_tac_online
   ```

7. Create new alembic revision (autogenerate)

   ```
   alembic revision --autogenerate -m "Add all tables"
   alembic upgrade head
   ```

   This will create the tables in the database.

8. Run the application

   ```
   uvicorn server:app --reload
   ```

   This will start the backend application on http://localhost:8000

9. (Optional) Run the frontend application

```
cd frontend
npm install
npm run dev
```

This will start the frontend application on http://localhost:3000

# Run the tests

```
pytest tests/
```

This will run the tests and generate a coverage report.

# Run the simulation

1. Run the simulation
   ```
   python simulation/run_simulation.py
   ```
