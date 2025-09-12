# 🗄️ Database Setup Guide

## Overview
Your RAG Multi-Tenant system now uses **SQLite** for persistent storage instead of JSON files. This ensures your tenant data persists across deployments on Render.

## ✅ What's Been Implemented

### 1. **SQLite Database Module** (`app/database.py`)
- Complete database schema for tenants, documents, and statistics
- Automatic migration from JSON files
- Optimized queries with indexes
- Error handling and logging

### 2. **Updated Multi-Tenant System** (`app/multi_tenant.py`)
- All methods now use database instead of in-memory storage
- Automatic migration on startup
- Backward compatibility with existing JSON files

### 3. **Database Initialization** (`init_database.py`)
- Standalone script to initialize database
- Migrates existing JSON data automatically
- Can be run manually for testing

### 4. **Enhanced Server Startup** (`start_server.py`)
- Automatic database initialization on server start
- Migration from JSON files if they exist
- Error handling for database setup

## 🚀 Deployment on Render

### Automatic Setup
Your app will automatically:
1. ✅ Create SQLite database on first run
2. ✅ Migrate existing JSON data (if any)
3. ✅ Initialize all tables and indexes
4. ✅ Start serving requests

### No Additional Configuration Needed
- SQLite is built into Python (no extra dependencies)
- Database file persists on Render's filesystem
- No environment variables required
- No external database setup needed

## 📁 Database File
- **Location**: `rag_database.db` (in your app root)
- **Size**: Typically < 1MB for small to medium apps
- **Backup**: Automatically backed up with your code

## 🔄 Migration Process

### From JSON Files (Automatic)
If you have existing JSON files:
- `tenants.json` → `tenants` table
- `tenant_documents.json` → `tenant_documents` table  
- `tenant_stats.json` → `tenant_stats` table

### Migration Steps
1. App starts up
2. Detects JSON files exist
3. Migrates all data to database
4. Continues normal operation
5. JSON files remain as backup

## 🧪 Testing

### Run Database Tests
```bash
python test_database.py
```

### Manual Database Initialization
```bash
python init_database.py
```

## 📊 Database Schema

### Tables Created
1. **tenants** - Tenant configurations and settings
2. **tenant_documents** - All uploaded documents with chunks
3. **tenant_stats** - Analytics and usage statistics

### Indexes for Performance
- Tenant domain lookup
- API key authentication
- Document search by tenant
- Upload time sorting

## 🔧 Maintenance

### Database Backup
The database file (`rag_database.db`) is included in your deployment and will be backed up with your code.

### Monitoring
Check logs for database operations:
- Tenant creation/deletion
- Document uploads
- Query statistics
- Migration status

## 🆓 Free Tier Benefits

### Render Free Tier
- ✅ **Persistent storage** - Database survives app restarts
- ✅ **No external dependencies** - SQLite is built-in
- ✅ **No additional costs** - Completely free
- ✅ **Automatic scaling** - Handles multiple tenants
- ✅ **Data integrity** - ACID transactions

### Limitations
- Database file size limited by Render's storage
- Single database file (no clustering)
- No built-in replication

## 🚨 Important Notes

1. **First Deployment**: Database will be created automatically
2. **Existing Data**: JSON files will be migrated on first run
3. **Backup**: Keep JSON files as backup until you're confident
4. **Monitoring**: Check Render logs for database operations
5. **Performance**: SQLite handles thousands of tenants efficiently

## 🎯 Next Steps

1. **Deploy to Render** - Your app is ready!
2. **Test tenant creation** - Verify persistence
3. **Monitor logs** - Check database operations
4. **Remove JSON files** - Once you're confident (optional)

---

**Your RAG system now has persistent, free database storage! 🎉**
