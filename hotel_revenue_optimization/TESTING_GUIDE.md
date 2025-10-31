# Testing Guide - Hotel Revenue Optimization System

This guide provides comprehensive testing examples to validate the enhanced input processing capabilities and error handling of the Hotel Revenue Optimization System v2.0.

## Quick Validation Tests

### 1. System Status Check
```bash
# Verify the agent is running
agentcore status
```

### 2. Basic Hotel Analysis Test
```bash
# Test with structured input
agentcore invoke '{
  "hotel_name": "The Grand Hotel",
  "hotel_location": "Chicago, IL",
  "current_adr": "$200",
  "historical_occupancy": "70%",
  "target_revpar": "10% increase"
}'
```

## Input Format Testing

### Prompt-Based Format
```bash
# Natural language hotel analysis
agentcore invoke '{"prompt": "Analyze revenue optimization for The Ritz-Carlton in San Francisco. Current ADR is $450, occupancy at 68%, targeting 15% RevPAR increase over next quarter."}'

# Boutique hotel example
agentcore invoke '{"prompt": "Help me optimize revenue for my boutique hotel in Miami. We have 120 rooms, current ADR $280, occupancy 65%. Struggling with weekday bookings."}'

# Luxury resort example
agentcore invoke '{"prompt": "I need help optimizing revenue for my luxury resort in Aspen. We have 200 rooms, current ADR is $650, occupancy around 55% in shoulder season."}'
```

### Message-Based Format
```bash
# Casual message format
agentcore invoke '{"message": "Can you help me with pricing strategy for my hotel in Las Vegas? We are a 4-star property with 300 rooms."}'

# Detailed message format
agentcore invoke '{"message": "Looking for revenue optimization advice. My hotel is The Oceanview Resort in Santa Monica, 150 rooms, current ADR $380, occupancy 72%."}'
```

### Structured JSON Format
```bash
# Complete structured input
agentcore invoke '{
  "hotel_name": "Mountain View Lodge",
  "hotel_location": "Aspen, CO",
  "room_count": "200",
  "current_adr": "$650",
  "historical_occupancy": "55%",
  "season": "shoulder season",
  "target_revpar": "20% increase",
  "current_challenges": "Low weekday occupancy, high operational costs"
}'

# Minimal structured input
agentcore invoke '{
  "hotel_name": "City Center Hotel",
  "hotel_location": "Seattle, WA",
  "current_adr": "$180",
  "historical_occupancy": "68%"
}'
```

## Error Handling Testing

### Irrelevant Query Detection
```bash
# Weather query
agentcore invoke '{"prompt": "What is the weather forecast for tomorrow?"}'

# General travel question
agentcore invoke '{"prompt": "What are the best tourist attractions in Paris?"}'

# Political question
agentcore invoke '{"prompt": "What do you think about the current political situation?"}'

# Technology question
agentcore invoke '{"message": "How do I fix my computer?"}'
```

**Expected Response Format:**
```json
{
  "error": "irrelevant_query",
  "message": "I specialize in hotel revenue optimization. I can help with pricing strategies, demand forecasting, and revenue management.",
  "capabilities": [
    "Hotel pricing optimization",
    "Revenue forecasting",
    "Market analysis",
    "Demand prediction"
  ]
}
```

### Booking Request Detection
```bash
# Direct booking request
agentcore invoke '{"prompt": "I want to book a room for next weekend at a hotel in Miami"}'

# Reservation inquiry
agentcore invoke '{"message": "Can you help me make a reservation for 2 nights in New York?"}'

# Availability check
agentcore invoke '{"prompt": "Do you have any rooms available for December 15th?"}'
```

**Expected Response Format:**
```json
{
  "error": "booking_request",
  "message": "I don't handle hotel bookings. I specialize in revenue optimization for hotel operators.",
  "suggestion": "For bookings, please contact the hotel directly or use booking platforms."
}
```

### Insufficient Information Handling
```bash
# Vague request
agentcore invoke '{"prompt": "Help me with my hotel"}'

# Missing key details
agentcore invoke '{"message": "I need revenue optimization advice"}'

# Incomplete information
agentcore invoke '{"prompt": "My hotel is not performing well"}'
```

**Expected Response Format:**
```json
{
  "error": "insufficient_information",
  "message": "I need more specific hotel information to provide revenue optimization analysis.",
  "required_info": [
    "Hotel name or property details",
    "Location (city/region)",
    "Current performance metrics (ADR, occupancy, RevPAR)"
  ],
  "example": "Analyze revenue for The Grand Hotel in Chicago. Current ADR $200, occupancy 70%."
}
```

## Natural Language Processing Tests

### Hotel Name Extraction
```bash
# Various hotel name formats
agentcore invoke '{"prompt": "Revenue analysis for Marriott Downtown Seattle, ADR $220, occupancy 75%"}'
agentcore invoke '{"prompt": "Help with The Four Seasons Beverly Hills pricing strategy"}'
agentcore invoke '{"prompt": "Optimize revenue for Hilton Garden Inn Chicago O Hare"}'
```

### Location Detection
```bash
# Different location formats
agentcore invoke '{"prompt": "Hotel in NYC needs revenue optimization, current ADR $300"}'
agentcore invoke '{"prompt": "My San Francisco property has 68% occupancy"}'
agentcore invoke '{"prompt": "Resort in Miami Beach, Florida needs pricing help"}'
```

### Metric Parsing
```bash
# Various metric formats
agentcore invoke '{"prompt": "ADR of $450, occupancy rate 68%, need 15% RevPAR boost"}'
agentcore invoke '{"prompt": "Average daily rate: $280, occupancy: 72 percent"}'
agentcore invoke '{"prompt": "Current RevPAR is $176, targeting $195"}'
```

## Edge Case Testing

### Mixed Content
```bash
# Hotel request with irrelevant content
agentcore invoke '{"prompt": "I love the weather today! Can you help optimize revenue for my hotel in Denver? ADR is $180."}'

# Multiple hotels mentioned
agentcore invoke '{"prompt": "Compare revenue strategies for The Ritz-Carlton and Marriott properties in San Francisco"}'
```

### Malformed Input
```bash
# Missing quotes
agentcore invoke '{prompt: "Help with hotel revenue"}'

# Invalid JSON structure
agentcore invoke '{"prompt": "Hotel analysis", "extra_field"}'
```

## Performance Testing

### Response Time Validation
```bash
# Time the response
time agentcore invoke '{"prompt": "Analyze revenue for The Grand Hotel in Chicago. Current ADR $200, occupancy 70%."}'
```

### Concurrent Requests
```bash
# Test multiple simultaneous requests
for i in {1..5}; do
  agentcore invoke '{"prompt": "Revenue analysis for Hotel '$i' in City '$i'"}' &
done
wait
```

## Log Monitoring During Tests

### Real-time Log Monitoring
```bash
# Monitor logs while testing
aws logs tail /aws/bedrock-agentcore/runtimes/hotel_revenue_optimization-2OYNqEGtl3-DEFAULT --follow
```

### Error Log Analysis
```bash
# Check for errors in recent logs
aws logs tail /aws/bedrock-agentcore/runtimes/hotel_revenue_optimization-2OYNqEGtl3-DEFAULT --since 1h | grep -i error
```

## Validation Checklist

### ✅ Core Functionality
- [ ] Hotel-specific analysis (not hardcoded Miami responses)
- [ ] Natural language input processing
- [ ] Structured JSON input support
- [ ] Prompt and message format handling

### ✅ Error Handling
- [ ] Irrelevant query detection
- [ ] Booking request redirection
- [ ] Insufficient information guidance
- [ ] Malformed input handling

### ✅ NLP Capabilities
- [ ] Hotel name extraction
- [ ] Location detection
- [ ] Metric parsing (ADR, occupancy, RevPAR)
- [ ] Context understanding

### ✅ System Health
- [ ] Agent status operational
- [ ] Response times acceptable (<30 seconds)
- [ ] Logs showing proper processing
- [ ] No system errors or crashes

## Troubleshooting

### Common Issues

1. **Agent Not Responding**
   ```bash
   agentcore status
   # If not running, redeploy
   agentcore launch
   ```

2. **Timeout Errors**
   - Check AWS credentials
   - Verify Bedrock model access
   - Monitor CloudWatch logs

3. **Unexpected Responses**
   - Verify input format
   - Check for typos in JSON
   - Review recent logs for errors

### Getting Help

If tests fail or you encounter issues:

1. Check the [CHANGELOG.md](CHANGELOG.md) for recent changes
2. Review logs: `aws logs tail /aws/bedrock-agentcore/runtimes/hotel_revenue_optimization-2OYNqEGtl3-DEFAULT --since 1h`
3. Verify agent status: `agentcore status`
4. Test with simple structured input first
5. Escalate to development team with specific error messages and logs
