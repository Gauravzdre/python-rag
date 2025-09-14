# 🤖 RAG Chatbot Embedding Guide

This guide shows you how to embed your RAG chatbot into any website.

## 🚀 Quick Start

### 1. Start Your RAG Server
```bash
python start_server.py
```

### 2. Create a Tenant
1. Go to `http://localhost:8000`
2. Click "Add Tenant" 
3. Fill in your company details
4. Note the tenant ID

### 3. Upload Documents
1. Select your tenant
2. Upload documents (PDF, TXT, MD, JSON)
3. Wait for processing to complete

### 4. Embed in Your Website

Add this script tag to your website's HTML:

```html
<script src="http://localhost:8000/rag-widget.js" 
        data-api-url="http://localhost:8000" 
        data-tenant-id="your-tenant-id"
        data-title="Your AI Assistant">
</script>
```

## 📋 Configuration Options

| Attribute | Description | Default |
|-----------|-------------|---------|
| `data-api-url` | Your RAG API server URL | `http://localhost:8000` |
| `data-tenant-id` | Your tenant ID | `default` |
| `data-title` | Chatbot title | `AI Assistant` |
| `data-position` | Widget position | `bottom-right` |
| `data-theme` | Color theme | `default` |

## 🎨 Customization

### Custom Styling
The widget uses CSS that can be overridden:

```css
#rag-chatbot-widget {
    /* Custom styles */
    border-radius: 20px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.3);
}

#rag-toggle-btn {
    /* Custom button styles */
    background: #your-color !important;
}
```

### Custom Messages
You can customize the welcome message by modifying the widget code.

## 🔧 Advanced Setup

### For Production
1. Deploy your RAG server to a public URL
2. Update the `data-api-url` to your production server
3. Consider using HTTPS for security
4. Set up proper CORS policies

### Multiple Tenants
Each website can have its own tenant:
- Create separate tenants for different websites
- Use different `data-tenant-id` values
- Upload tenant-specific documents

### API Endpoints

#### Public Endpoints (No Auth Required)
- `GET /embed-token` - Get embed token
- `POST /embed/query` - Send query (no auth)

#### Authenticated Endpoints
- `GET /get-token` - Get JWT token
- `POST /query/tenant` - Send authenticated query

## 📱 Mobile Responsive

The widget automatically adapts to mobile devices:
- Full screen on mobile
- Touch-friendly interface
- Responsive design

## 🛠️ Troubleshooting

### Common Issues

1. **Widget not appearing**
   - Check browser console for errors
   - Verify API URL is correct
   - Ensure server is running

2. **"Not connected" error**
   - Check if server is accessible
   - Verify CORS settings
   - Check network connectivity

3. **No responses**
   - Verify tenant ID is correct
   - Check if documents are uploaded
   - Look at server logs

### Debug Mode
Add `data-debug="true"` to see console logs:

```html
<script src="rag-widget.js" 
        data-api-url="http://localhost:8000" 
        data-tenant-id="your-tenant-id"
        data-debug="true">
</script>
```

## 🔒 Security Considerations

1. **CORS**: Server allows all origins for embedding
2. **Rate Limiting**: Consider adding rate limits
3. **Input Validation**: Server validates all inputs
4. **HTTPS**: Use HTTPS in production

## 📊 Analytics

Track chatbot usage:
- Monitor API endpoints
- Log query patterns
- Track tenant usage

## 🎯 Use Cases

- **Customer Support**: Answer common questions
- **Product Information**: Provide product details
- **Documentation**: Help users find information
- **Lead Generation**: Qualify potential customers

## 📞 Support

For issues or questions:
1. Check the server logs
2. Review browser console
3. Test with the example page
4. Verify tenant setup

## 🚀 Next Steps

1. **Customize the widget** for your brand
2. **Add more documents** to improve responses
3. **Monitor usage** and optimize
4. **Scale up** as needed

Happy embedding! 🎉
