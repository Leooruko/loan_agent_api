# GreenCom Loan Assistant API

A modern, user-friendly AI-powered loan data analysis system that provides intelligent insights into loan portfolios, payment trends, and client behavior.

## 🚀 Features

### Enhanced User Experience
- **Modern Chat Interface**: Beautiful, responsive design with smooth animations
- **Smart Loading States**: Animated typing indicators and progress feedback
- **Error Handling**: User-friendly error messages and graceful failure recovery
- **Quick Suggestions**: Pre-built question chips for common queries
- **Real-time Feedback**: Immediate visual feedback for all user interactions

### Improved AI Capabilities
- **Conversational AI**: Friendly, approachable language that's easy to understand
- **Smart Error Recovery**: Handles complex queries and provides helpful suggestions
- **Context Awareness**: Maintains conversation context for better responses
- **Data Validation**: Robust input validation and query safety checks

### Advanced Data Analysis
- **Loan Portfolio Insights**: Comprehensive analysis of loan performance
- **Payment Trend Analysis**: Identify patterns in payment behavior
- **Client Behavior Tracking**: Monitor client engagement and risk factors
- **Manager Performance**: Track loan manager effectiveness
- **Product Analysis**: Understand which loan products perform best

## 🛠️ Technical Improvements

### System Prompt Enhancements
- **Simplified Instructions**: Clear, concise prompts that reduce processing time
- **Better Error Handling**: Graceful handling of non-dataset questions
- **User-Friendly Language**: Conversational tone that's relatable and engaging
- **Focused Capabilities**: Streamlined to handle loan-specific queries efficiently

### Tool Functionality
- **Enhanced Validation**: Comprehensive input validation and safety checks
- **Query Complexity Limits**: Prevents overly complex queries that could slow the system
- **Better Error Messages**: Clear, actionable error messages for users
- **Data Safety**: Protected against malicious or invalid queries

### API Improvements
- **Comprehensive Error Handling**: Proper HTTP status codes and error messages
- **Input Validation**: Request validation and sanitization
- **Logging**: Detailed logging for monitoring and debugging
- **Health Checks**: System health monitoring endpoints
- **API Documentation**: Clear endpoint documentation and usage examples

## 📊 Available Data Fields

The system can analyze the following loan data:

| Field | Description |
|-------|-------------|
| `Managed_By` | Loan manager name |
| `Loan_No` | Unique loan identifier |
| `Loan_Product_Type` | Type of loan product |
| `Client_Code` | Unique client identifier |
| `Client_Name` | Client's name |
| `Issued_Date` | When loan was issued |
| `Amount_Disbursed` | Loan amount given to client |
| `Installments` | Total number of installments |
| `Total_Paid` | Amount client has paid so far |
| `Total_Charged` | Total amount owed (principal + interest) |
| `Days_Since_Issued` | Days since loan was issued |
| `Is_Installment_Day` | Whether today is a payment day |
| `Weeks_Passed` | Weeks since loan was issued |
| `Installments_Expected` | Expected payments by now |
| `Installment_Amount` | Amount per payment |
| `Expected_Paid_Today` | Expected payment for today |
| `Expected_Before_Today` | Expected total payments by now |
| `Arrears` | Unpaid amount |
| `Due_Today` | Amount due today |
| `Mobile_Phone_No` | Client's phone number |
| `Status` | Loan status (Active, Closed, etc.) |
| `Client_Loan_Count` | Total loans client has had |
| `Client_Type` | Individual or Group loan |

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Ollama with Mistral model installed
- Required Python packages (see requirements.txt)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd loan_agent_api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Ollama with Mistral model**
   ```bash
   ollama pull mistral
   ollama run mistral
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Web Interface: http://localhost:5500
   - API Health Check: http://localhost:5500/health
   - API Info: http://localhost:5500/api/info

## 💬 Example Queries

### Portfolio Overview
- "How many active loans do we have?"
- "What is our total loan portfolio value?"
- "Show me the distribution of loan amounts"

### Payment Analysis
- "Which clients have the highest arrears?"
- "Show me payment trends over time"
- "What's the average payment rate?"

### Client Insights
- "Show me clients with multiple loans"
- "Which clients are most at risk?"
- "What's the average loan amount per client type?"

### Manager Performance
- "Which loan managers have the most clients?"
- "Show me manager performance metrics"
- "Who manages the highest value loans?"

### Product Analysis
- "What are our most popular loan products?"
- "Which product types have the best repayment rates?"
- "Show me product performance comparison"

## 🔧 API Endpoints

### Chat Endpoint
```http
POST /chat
Content-Type: application/json

{
  "promt": "How many active loans do we have?",
  "history": []
}
```

### Health Check
```http
GET /health
```

### API Information
```http
GET /api/info
```

## 🎨 UI Features

### Modern Design
- **Gradient Backgrounds**: Beautiful visual appeal
- **Card-based Layout**: Clean, organized interface
- **Responsive Design**: Works on all device sizes
- **Smooth Animations**: Professional user experience

### Interactive Elements
- **Suggestion Chips**: Quick access to common queries
- **Typing Indicators**: Real-time feedback during processing
- **Error States**: Clear error messages with helpful suggestions
- **Loading States**: Visual feedback for all operations

### User Experience
- **Auto-scroll**: Automatically scrolls to new messages
- **Input Validation**: Prevents empty or invalid submissions
- **Keyboard Shortcuts**: Enter key to send messages
- **Focus Management**: Automatic focus on input field

## 🔒 Security & Performance

### Security Features
- **Input Sanitization**: All user inputs are validated and sanitized
- **Query Limits**: Prevents overly complex or malicious queries
- **Error Handling**: Graceful handling of all error conditions
- **Data Protection**: Secure handling of sensitive loan data

### Performance Optimizations
- **Query Complexity Limits**: Prevents system overload
- **Efficient Data Loading**: Optimized CSV data access
- **Async Processing**: Non-blocking request handling
- **Memory Management**: Efficient resource utilization

## 🐛 Troubleshooting

### Common Issues

1. **Model Not Responding**
   - Ensure Ollama is running with Mistral model
   - Check if the model is properly loaded
   - Verify network connectivity

2. **Data Not Loading**
   - Ensure `processed_data.csv` exists in the project root
   - Check file permissions
   - Verify CSV format is correct

3. **Slow Responses**
   - Check system resources (CPU, memory)
   - Verify Ollama model performance
   - Consider simplifying complex queries

### Error Messages

- **"I can only help with loan data questions"**: Ask about loans, payments, or clients
- **"Query too complex"**: Simplify your question
- **"Network connection issue"**: Check your internet connection
- **"Processing timeout"**: Try again with a simpler question

## 📈 Future Enhancements

- **Data Visualization**: Charts and graphs for better insights
- **Export Functionality**: Download reports and analysis
- **User Authentication**: Secure access control
- **Real-time Updates**: Live data synchronization
- **Mobile App**: Native mobile application
- **Advanced Analytics**: Machine learning insights

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above

---

**GreenCom Loan Assistant** - Making loan data analysis simple and insightful! 🚀 