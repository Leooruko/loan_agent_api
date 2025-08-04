# Timeout Troubleshooting Guide

## 🚨 **Worker Timeout Error**

### **Error Message:**
```
[CRITICAL] WORKER TIMEOUT (pid:2605)
Error handling request /chat
SystemExit: 1
```

### **What This Means:**
- Gunicorn worker process took too long to respond
- Worker was killed by Gunicorn due to timeout
- Request processing exceeded the default 30-second timeout

## 🔍 **Root Causes**

### **1. AI Processing Time**
- **LLM Response Time**: Mistral model takes time to process complex queries
- **Agent Iterations**: Multiple tool calls and reasoning steps
- **Data Analysis**: Large dataset queries and processing

### **2. Gunicorn Configuration**
- **Default Timeout**: 30 seconds (too short for AI workloads)
- **Worker Management**: Insufficient worker processes
- **Resource Limits**: Memory or CPU constraints

### **3. Query Complexity**
- **Complex Questions**: Multi-step analysis requests
- **Large Datasets**: Queries returning many rows
- **Tool Usage**: Multiple fetch_data calls

## 🛠️ **Solutions**

### **Solution 1: Use Production Startup (Recommended)**

```bash
# Install Gunicorn
pip install gunicorn==21.2.0

# Start with optimized configuration
python start_production.py
```

**Benefits:**
- ✅ 120-second timeout (vs 30-second default)
- ✅ Optimized worker configuration
- ✅ Better resource management
- ✅ Comprehensive logging

### **Solution 2: Manual Gunicorn with Timeout**

```bash
# Start with extended timeout
gunicorn --bind 0.0.0.0:5500 --timeout 120 --workers 3 app:app
```

### **Solution 3: Development Mode (Testing)**

```bash
# Use Flask development server (no timeout issues)
python app.py
```

## ⚙️ **Configuration Optimizations**

### **Updated AI Configuration:**
```python
AI_CONFIG = {
    'TIMEOUT_SECONDS': 90,     # 90 seconds for AI processing
    'REQUEST_TIMEOUT': 100,    # 100 seconds total request time
    'MAX_ITERATIONS': 6,       # Reduced to prevent excessive processing
    'TEMPERATURE': 0.1,        # Lower temperature for faster responses
}
```

### **Gunicorn Configuration:**
```python
# gunicorn_config.py
timeout = 120              # 2 minutes
workers = 3                # Optimal for AI workloads
worker_class = "sync"      # Better for CPU-intensive tasks
preload_app = True         # Faster startup
```

## 📊 **Performance Monitoring**

### **Check Response Times:**
```bash
# Monitor logs for response times
tail -f logs/loan_assistant.log | grep "response generated successfully"
```

### **Monitor Gunicorn:**
```bash
# Check worker status
ps aux | grep gunicorn

# Monitor resource usage
htop
```

## 🔧 **Quick Fixes**

### **Immediate Fix:**
1. **Stop current server**: `Ctrl+C`
2. **Install Gunicorn**: `pip install gunicorn==21.2.0`
3. **Start with timeout**: `gunicorn --timeout 120 app:app`
4. **Test**: Send a simple query

### **If Still Timing Out:**
1. **Reduce complexity**: Ask simpler questions
2. **Check Ollama**: Ensure Mistral is running
3. **Monitor resources**: Check CPU/memory usage
4. **Use development mode**: For testing without timeouts

## 🚀 **Production Deployment**

### **Using start_production.py:**
```bash
python start_production.py
# Choose option 1 (Production mode)
```

### **Manual Production:**
```bash
gunicorn --config gunicorn_config.py app:app
```

### **Docker (if needed):**
```dockerfile
# Add to Dockerfile
RUN pip install gunicorn==21.2.0
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
```

## 📈 **Performance Tips**

### **1. Optimize Queries:**
- Ask specific questions
- Avoid overly complex requests
- Use simple language

### **2. Monitor Usage:**
- Check response times in logs
- Monitor worker processes
- Watch resource consumption

### **3. Scale Appropriately:**
- Increase workers for high load
- Adjust timeout based on usage
- Monitor and optimize

## 🔍 **Debugging Steps**

### **Step 1: Check Logs**
```bash
# Application logs
tail -f logs/loan_assistant.log

# Gunicorn logs
tail -f logs/gunicorn_error.log
```

### **Step 2: Test Simple Query**
```bash
curl -X POST http://localhost:5500/chat \
  -H "Content-Type: application/json" \
  -d '{"promt": "Hello"}'
```

### **Step 3: Check Ollama**
```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test Mistral model
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral", "prompt": "Hello"}'
```

### **Step 4: Monitor Resources**
```bash
# Check CPU and memory
top

# Check disk space
df -h

# Check network
netstat -tulpn | grep 5500
```

## 🎯 **Prevention**

### **1. Use Production Mode:**
- Always use `start_production.py` for production
- Configure appropriate timeouts
- Monitor performance

### **2. Optimize Queries:**
- Keep questions specific and simple
- Avoid multi-step complex requests
- Use clear, direct language

### **3. Regular Monitoring:**
- Check response times
- Monitor worker health
- Review error logs

## 📞 **Support**

### **If Issues Persist:**
1. Check `logs/loan_assistant.log` for detailed errors
2. Review `logs/gunicorn_error.log` for worker issues
3. Test with simple queries first
4. Ensure Ollama and Mistral are running properly

### **Common Solutions:**
- ✅ Use production startup script
- ✅ Increase timeout values
- ✅ Reduce query complexity
- ✅ Monitor resource usage
- ✅ Check Ollama status

---

**Remember**: The timeout issue is primarily due to AI processing time, not a bug in the code. The solutions above optimize the system for AI workloads with longer processing times. 