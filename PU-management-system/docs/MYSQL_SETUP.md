# 🗄️ MySQL Setup Instructions - Poornima University Management System

## Step 1: Download MySQL Server 8.0

### Option A: Direct Download (Recommended)
1. Visit: https://dev.mysql.com/downloads/mysql/
2. Select "Windows (x86, 64-bit)" - MySQL Community Server 8.0.x
3. Click "Download" (you may need to create a free account)
4. Choose "No thanks, just start my download"

### Option B: Direct Link
- Download: https://dev.mysql.com/get/Downloads/mysql-installer-web/mysql-installer-web-8.0.exe

---

## Step 2: Install MySQL Server

### During Installation:
1. **Setup Type**: Choose "Developer Default" (includes MySQL Server, Workbench, MySQL Shell)
2. **MySQL Server Configuration**:
   - Port: **3306** (default)
   - Config Type: **Development Machine**
3. **MySQL Server 8.0.x - Server Configuration**:
   - Standalone MySQL Server / Classic MySQL Replication
   - Config Server Type: **Development Machine**
   - MySQL Port: **3306**
   - MySQL User: **root**
4. **Accounts and Roles**:
   - **☑️ IMPORTANT**: Set root password (e.g., `your_password_here`)
   - Note: You'll need this password for the setup script!
5. **Windows Service**: Let it install as Windows Service (auto-start)
6. **Complete Install**

### After Installation:
- MySQL Server should start automatically
- You can verify via Windows Services (services.msc)

---

## Step 3: Verify MySQL Installation

### In PowerShell:
```powershell
# Test MySQL version
mysql --version

# Test connection (may ask for password)
mysql -u root -p

# Exit MySQL prompt
exit
```

### Expected Output:
```
mysql  Ver 8.0.x for Win64 on x86_64
```

---

## Step 4: Run Automated Database Setup

Once MySQL is installed and verified:

### In PowerShell:
```powershell
# Navigate to project directory
cd C:\Poornima_university_management_system

# Run setup script (make sure MySQL service is running)
.\setup_database.ps1
```

### What the Script Does:
✅ Tests MySQL connection  
✅ Creates `university_db` database  
✅ Creates all 17 tables with relationships  
✅ Sets up indexes for optimization  
✅ Optionally inserts sample data  

---

## Step 5: Configure Environment Variables

The script will prompt you for the MySQL root password.

After setup, update `.env` file:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password_here        # ← Use the password you set during install
DB_NAME=university_db
```

---

## Troubleshooting

### Problem: "MySQL is not recognized as an internal or external command"
**Solution**: 
1. Verify MySQL was installed to: `C:\Program Files\MySQL\MySQL Server 8.0`
2. Restart PowerShell after installation
3. Add MySQL to PATH:
   ```powershell
   $env:Path += ';C:\Program Files\MySQL\MySQL Server 8.0\bin'
   ```

### Problem: "Access denied for user 'root'@'localhost'"
**Solution**:
1. Verify password is correct
2. Test directly in MySQL Command Line Client:
   ```bash
   mysql -u root -p
   ```
3. If MySQL is running: check Windows Services (services.msc)

### Problem: "Can't connect to MySQL server on 'localhost' (10061)"
**Solution**:
1. MySQL Service may not be running
2. Start it: `net start MySQL80` (in admin PowerShell)
3. Or use Services app: `services.msc` → Find "MySQL80" → Right-click → Start

---

## Manual Database Setup (If Script Fails)

If the PowerShell script doesn't work, use MySQL Workbench:

1. Open MySQL Workbench
2. New SQL Tab: Ctrl+T
3. Open file: `database\university-db.sql`
4. Execute: Ctrl+Shift+Enter
5. Verify: Check Schemas panel (refresh if needed)

---

## Next Steps After Setup

Once database is ready:
1. ✅ Update `.env` file
2. ✅ Start backend: `python backend/server.py`
3. ✅ Test endpoints via frontend
4. ✅ Login with sample credentials

---

## Default Test Credentials (If Sample Data Installed)

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- Email: `admin@university.edu`

---

**Questions?** Check the logs in setup_database.ps1 or review MySQL error messages carefully.
