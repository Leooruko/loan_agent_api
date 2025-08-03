# Troubleshooting Guide - Brightcom Loan Assistant API v2.0

This guide helps you resolve common issues with the loan agent system.

## 🚨 Quick Fixes

### System Won't Start
1. **Check Python version**: `python --version` (needs 3.8+)
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Check data file**: Ensure `processed_data.csv` exists
4. **Start Ollama**: `ollama serve` then `ollama pull mistral`

### Model Not Responding
1. **Check Ollama**: `curl http://localhost:11434/api/tags`
2. **Restart Ollama**: `ollama serve`
3. **Check model**: `ollama list` (should show mistral)
4. **Pull model**: `ollama pull mistral`

### Slow Performance
1. **Check system resources**: CPU, memory usage
2. **Simplify queries**: Use shorter, more specific questions
3. **Check logs**: Review `logs/loan_assistant.log`
4. **Restart application**: Stop and restart the server

## 🔍 Detailed Troubleshooting

### 1. Installation Issues

#### Python Version Error
```
❌ Error: Python 3.8 or higher is required
```

**Solution:**
- Update Python to version 3.8 or higher
- Use virtual environment: `python -m venv venv && source venv/bin/activate`

#### Missing Dependencies
```
❌ Missing packages: flask, langchain, pandas
```

**Solution:**
```bash
pip install -r requirements.txt
```

#### Permission Errors
```
❌ Permission denied: logs/
```

**Solution:**
```bash
mkdir logs
chmod 755 logs
```

### 2. Data Issues

#### Data File Not Found
```
❌ Data file not found: processed_data.csv
```

**Solution:**
- Ensure `processed_data.csv` is in the project root
- Check file permissions
- Verify CSV format is correct

#### Data Loading Errors
```
❌ Error loading data: [Errno 2] No such file or directory
```

**Solution:**
- Check file path in `config.py`
- Verify file encoding (should be UTF-8)
- Check file size (should not be empty)

#### CSV Format Issues
```
❌ Error: Invalid CSV format
```

**Solution:**
- Open CSV in text editor to check format
- Ensure proper comma separation
- Check for missing headers

### 3. Ollama Issues

#### Ollama Not Running
```
❌ Ollama is not running
```

**Solution:**
```bash
# Start Ollama
ollama serve

# In another terminal, pull and run Mistral
ollama pull mistral
ollama run mistral
```

#### Model Not Found
```
⚠️ Ollama is running but Mistral model not found
```

**Solution:**
```bash
# Pull the Mistral model
ollama pull mistral

# Verify model is available
ollama list
```

#### Connection Timeout
```
❌ Connection timeout to Ollama
```

**Solution:**
- Check if Ollama is running on port 11434
- Restart Ollama: `pkill ollama && ollama serve`
- Check firewall settings
- Verify network connectivity

### 4. Application Issues

#### Flask Server Won't Start
```
❌ Error starting application: Address already in use
```

**Solution:**
```bash
# Find and kill process using port 5500
lsof -ti:5500 | xargs kill -9

# Or use different port in config.py
```

#### Import Errors
```
❌ ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt
pip install -r requirements.txt
```

#### Memory Issues
```
❌ Memory error or system crash
```

**Solution:**
- Close other applications
- Restart the system
- Check available RAM
- Reduce query complexity

### 5. Query Issues

#### Model Not Understanding Queries
```
❌ I'm having trouble understanding that question
```

**Solution:**
- Use simpler, more specific questions
- Ask about loan data specifically
- Use the suggested query examples
- Check the available data fields

#### SQL Query Errors
```
❌ Error: Invalid SQL syntax
```

**Solution:**
- Use simple SELECT queries only
- Reference the 'df' table
- Check column names in the data
- Use the query validation endpoint: `/api/validate-query`

#### Empty Results
```
❌ No data found matching your query
```

**Solution:**
- Check if data exists for your criteria
- Try broader queries first
- Verify column names and values
- Use the health check endpoint

### 6. Performance Issues

#### Slow Response Times
```
❌ Request timeout
```

**Solution:**
- Simplify your question
- Check system resources
- Restart the application
- Check Ollama performance

#### High Error Rates
```
❌ Multiple failed requests
```

**Solution:**
- Check logs for specific errors
- Restart Ollama and the application
- Verify data file integrity
- Check network connectivity

#### Rate Limiting
```
❌ Rate limit exceeded
```

**Solution:**
- Wait 1 minute between requests
- Reduce request frequency
- Check rate limit configuration

### 7. Log Analysis

#### Check Logs
```bash
# View recent logs
tail -f logs/loan_assistant.log

# Search for errors
grep "ERROR" logs/loan_assistant.log

# Check specific errors
grep "Exception" logs/loan_assistant.log
```

#### Common Log Messages

**INFO Messages (Normal):**
```
INFO - Processing query: How many active loans...
INFO - Data loaded successfully. Shape: (730, 23)
INFO - Chat response generated successfully in 2.34s
```

**WARNING Messages (Check):**
```
WARNING - Request timeout for client 127.0.0.1
WARNING - Query complexity limit reached
```

**ERROR Messages (Fix Required):**
```
ERROR - Data file not found
ERROR - Ollama connection failed
ERROR - Invalid SQL query
```

### 8. Testing and Validation

#### Run Test Script
```bash
python test_improvements.py
```

#### Check Health Endpoint
```bash
curl http://localhost:5500/health
```

#### Validate Queries
```bash
curl -X POST http://localhost:5500/api/validate-query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT COUNT(*) FROM df WHERE Status = \"Active\""}'
```

#### Check API Info
```bash
curl http://localhost:5500/api/info
```

## 🛠️ Advanced Troubleshooting

### Debug Mode
Enable debug mode in `config.py`:
```python
FLASK_CONFIG = {
    'DEBUG': True,
    # ... other settings
}
```

### Verbose Logging
Increase log level in `config.py`:
```python
LOGGING_CONFIG = {
    'LEVEL': 'DEBUG',
    # ... other settings
}
```

### Performance Monitoring
Check system resources:
```bash
# CPU and memory usage
top

# Disk space
df -h

# Network connections
netstat -tulpn | grep 5500
```

### Ollama Debugging
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check model details
ollama show mistral

# Test model directly
ollama run mistral "Hello, how are you?"
```

## 📞 Getting Help

If you're still experiencing issues:

1. **Check the logs**: `logs/loan_assistant.log`
2. **Run the test script**: `python test_improvements.py`
3. **Check system requirements**: Python 3.8+, sufficient RAM
4. **Verify Ollama setup**: Model downloaded and running
5. **Review this guide**: Look for similar error messages
6. **Create an issue**: Include logs and error messages

## 🔧 Configuration Tuning

### Performance Tuning
Edit `config.py` for better performance:
```python
AI_CONFIG = {
    'MAX_QUERY_LENGTH': 300,  # Reduce for faster processing
    'MAX_SQL_LENGTH': 200,    # Reduce for security
    'TIMEOUT_SECONDS': 30,    # Adjust timeout
    'MAX_ITERATIONS': 1,      # Reduce iterations
}
```

### Security Tuning
Adjust security settings:
```python
SECURITY_CONFIG = {
    'RATE_LIMIT_PER_MINUTE': 20,  # Reduce rate limit
    'MAX_QUERY_COMPLEXITY': 3,    # Reduce complexity
}
```

---

**Remember**: Most issues can be resolved by checking the logs and following the solutions above. If problems persist, the logs will provide specific error information to help identify the root cause. 