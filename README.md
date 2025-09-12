# 🚀 RAG Multi-Tenant Chatbot API

A powerful **Retrieval-Augmented Generation (RAG)** chatbot API built with FastAPI, featuring **multi-tenant support**, **PostgreSQL persistence**, and **advanced AI capabilities**.

## ✨ Features

- 🏢 **Multi-Tenant Architecture** - Support multiple companies in one application
- 📄 **Document Processing** - Upload and process various document types (PDF, TXT, etc.)
- 🧠 **Advanced RAG** - Enhanced retrieval with chunking and relevance scoring
- 🔐 **Dual Authentication** - JWT tokens + Tenant API keys
- ⚡ **Real-time Processing** - Fast document indexing and query responses
- 🐘 **PostgreSQL Persistence** - Free Neon database for production
- 🌐 **Production Ready** - Deploy on Render with zero configuration

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
export DATABASE_URL="your_neon_postgresql_url"
```

### 3. Run the Server
```bash
python start_server.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## 🔑 Key Endpoints

### Authentication
- `GET /get-token` - Generate JWT token for testing

### Document Management
- `POST /upload/tenant?tenant_id={id}` - Upload documents for tenant
- `GET /collection-info?tenant_id={id}` - Get tenant document info
- `GET /tenants/{tenant_id}/documents` - Get all tenant documents

### Query Processing
- `POST /query/tenant` - Ask questions about tenant documents

### Multi-Tenant Management (Admin)
- `POST /tenants/register` - Register new tenant
- `GET /tenants/` - List all tenants
- `GET /tenants/{tenant_id}` - Get tenant information
- `PUT /tenants/{tenant_id}` - Update tenant configuration
- `DELETE /tenants/{tenant_id}` - Delete tenant

## 🔧 Configuration

### Environment Variables
- `OPENROUTER_API_KEY` - Your OpenRouter API key for AI model access
- `DATABASE_URL` - PostgreSQL connection string (Neon)
- `JWT_SECRET` - Secret key for JWT token generation (default: "supersecret")

### Multi-Tenant Settings
Each tenant can be configured with:
- Company information (name, domain, email, phone)
- Plan limits (max documents, queries per day)
- AI personality and response style
- Custom branding (colors, logo, description)

## 🌐 Deployment

### Render.com (Recommended)
1. **Connect GitHub** - Link your repository to Render
2. **Set Environment Variables** - Add `OPENROUTER_API_KEY` in Render dashboard
3. **Deploy** - Everything else is pre-configured!

Your app will automatically:
- ✅ Connect to Neon PostgreSQL
- ✅ Create database tables
- ✅ Migrate existing data
- ✅ Start serving requests

### Environment Variables for Render
```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
DATABASE_URL=postgresql://neondb_owner:npg_b8wgFRi6fOTZ@ep-lively-haze-adxb4l5a-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

## 🏗️ Architecture

### Core Components
- **FastAPI Application** - Main API server with automatic docs
- **Multi-Tenant Engine** - Handles tenant isolation and management
- **PostgreSQL Database** - Persistent storage with Neon
- **Document Processor** - Processes and indexes uploaded documents
- **RAG Engine** - Retrieves relevant information and generates responses
- **Dual Authentication** - JWT + Tenant API key support

### Data Storage
- **PostgreSQL** - Persistent storage for tenants, documents, and statistics
- **Neon Database** - Free, cloud-hosted PostgreSQL (0.5GB storage, 10GB transfer/month)

## 📁 Project Structure
```
rag-app/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── multi_tenant.py         # Multi-tenant management
│   ├── postgres_database.py    # PostgreSQL database module
│   ├── rag_advanced.py         # Advanced RAG implementation
│   ├── rag_multi_tenant.py     # Multi-tenant RAG engine
│   ├── tenant_api.py           # Tenant management API
│   └── auth.py                 # Authentication system
├── requirements.txt            # Python dependencies
├── render.yaml                # Render deployment config
├── start_server.py            # Server startup script
└── web_interface.html         # Web interface
```

## 🔐 Authentication Methods

### 1. JWT Token (Admin/Web Interface)
```bash
curl -H "Authorization: Bearer <jwt_token>" \
     -X POST http://localhost:8000/query/tenant \
     -d '{"query": "What are your business hours?", "tenant_id": "omegagaze"}'
```

### 2. Tenant API Key (External Apps)
```bash
curl -H "Authorization: Bearer mt_42eb512a4b7d4e59" \
     -X POST http://localhost:8000/query/tenant \
     -d '{"query": "What are your business hours?", "tenant_id": "omegagaze"}'
```

## 🧪 Testing

### Test Your Deployment
```bash
# Test health check
curl https://your-app.onrender.com/healthcheck

# Test tenant query
curl -H "Authorization: Bearer mt_42eb512a4b7d4e59" \
     -H "Content-Type: application/json" \
     -X POST https://your-app.onrender.com/query/tenant \
     -d '{"query": "What are your business hours?", "tenant_id": "omegagaze"}'
```

## 🆓 Free Tier Benefits

### Neon PostgreSQL
- ✅ **0.5GB Storage** - Plenty for small to medium apps
- ✅ **10GB Transfer/month** - More than enough for most use cases
- ✅ **No time limits** - Truly free forever
- ✅ **Automatic backups** - Data safety guaranteed

### Render
- ✅ **750 hours/month** - Usually enough for small apps
- ✅ **512MB RAM** - Sufficient for RAG operations
- ✅ **Auto-wake** - Wakes up when accessed
- ✅ **SSL included** - Secure HTTPS by default

## 🚨 Important Notes

1. **First Deployment** - Database tables will be created automatically
2. **Data Migration** - JSON files will be migrated to PostgreSQL on first run
3. **API Keys** - Tenant API keys are preserved during migration
4. **Persistence** - All data now persists across deployments and restarts

## 📋 Next Steps

1. **Deploy to Render** - Your app is ready to deploy!
2. **Test External Integration** - Use tenant API keys for external apps
3. **Monitor Usage** - Check Render and Neon dashboards
4. **Scale as Needed** - Upgrade plans when you outgrow free tiers

## 🎯 External App Integration

Your external applications can now use:
- **Tenant API Key**: `mt_42eb512a4b7d4e59`
- **Tenant ID**: `omegagaze`
- **Base URL**: `https://your-app.onrender.com`

All endpoints support tenant API key authentication for seamless integration.

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions, please open an issue on GitHub.

---

**Ready to deploy? Your RAG system is production-ready with persistent PostgreSQL storage!** 🚀