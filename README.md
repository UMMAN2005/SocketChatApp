# SocketChatApp

![Screenshot 2024-11-24 205800](https://github.com/user-attachments/assets/d43ac35e-bc81-4c37-a136-c5b7bfd330e7)
![Screenshot 2024-11-24 205747](https://github.com/user-attachments/assets/aab0e584-a077-4c30-8382-ce0017eb8152)
![Screenshot 2024-11-24 205828](https://github.com/user-attachments/assets/4f6e92ab-fc8b-4744-b73f-0b755fddd990)
![Screenshot 2024-11-24 205845](https://github.com/user-attachments/assets/7729b934-03d8-40f6-a76b-a42255015530)
![Screenshot 2024-11-24 205902](https://github.com/user-attachments/assets/f1b7335e-8f25-4e94-9142-6ddbedeb4e98)
![Screenshot 2024-11-24 205941](https://github.com/user-attachments/assets/1d191a64-1c32-44b1-a142-4125d150561d)
![Screenshot 2024-11-24 210156](https://github.com/user-attachments/assets/cb2b861e-3d9e-49fd-a0db-7bdd5353d2ab)

## Setup

1. **Install uv**: Download and install `uv` using the appropriate command for your operating system:

   - **macOS and Linux**:

     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```

   - **Windows**:

     ```powershell
     irm https://astral.sh/uv/install.ps1 | iex
     ```

   Alternatively, if `pip` is available:

   ```bash
   pip install uv
   ```

2. **Navigate to the Project Directory**: Change into the directory of the cloned repository:

   ```bash
   cd SocketChatApp
   ```

3. **Install Dependencies**: Install the project's dependencies as specified in `pyproject.toml`:

   ```bash
   uv sync
   ```

4. **Set Env Variables**: Create .env file in this directory and add below variables:

   ```plaintext
    ENCRYPTION_KEY="8FpoN4h3XYcAZBeR3vim+xj0WVbduaUNkZE83SY+i1I="
    PASSWORD="<Your Actual Database Password>"
   ```

5. **Run Backend**: Execute the main script of backend:

   ```bash
   cd server
   uv run app.py
   ```

6. **Run Frontend**: In another terminal execute the main script of frontend:

   ```bash
   cd client
   uv run app.py
   ```
