1. Start environment:

   ```
   conda activate checkr-api
   ```

2. Start new Database:

   ```
   docker run -d --name checkr_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=checkr_db -p 9876:5432 postgres:latest
   ```

3. Connect to it on Postico:

   ```
   postgres://postgres:postgres@localhost:9876/checkr_db
   ```

4. Create new alembic revision (autogenerate)

   ```
   alembic revision --autogenerate -m "Add user account table"
   ```

5. Run the migration
   ```
   alembic upgrade head
   ```
