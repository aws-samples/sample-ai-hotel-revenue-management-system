# Knowledge Base - Hotel Revenue Optimization

This directory contains static knowledge base files that provide sample data for the Hotel Revenue Optimization System. These files serve as mock data sources for demonstration and development purposes.

## Current Knowledge Base Files

### 1. `competitor_pricing.txt`
- Contains competitor hotel pricing information
- Includes room rates, promotions, and market positioning data
- Used by Market Analyst agent for competitive analysis

### 2. `historical_booking_data.txt`
- Contains historical occupancy and booking patterns
- Includes seasonal trends and performance metrics
- Used by Demand Forecaster agent for trend analysis

### 3. `local_events.txt`
- Contains local events calendar and impact data
- Includes conventions, festivals, and business events
- Used by Demand Forecaster agent for event impact analysis

### 4. `revenue_management_best_practices.txt`
- Contains industry best practices and benchmarks
- Includes KPIs, strategies, and optimization guidelines
- Used by Revenue Manager agent for recommendations

## TODO: Production Integration Recommendations
============================================

### Replace Static Files with Dynamic Data Sources

#### 1. Competitor Pricing Data
**Current**: Static text file with sample competitor rates
**Production Goal**: Real-time competitor pricing feeds
**AgentCore Gateway Integration**:
- Connect to competitor rate shopping APIs (RateGain, OTA Insight, Travelclick)
- Create Lambda function to aggregate and normalize pricing data
- Implement scheduled updates (hourly/daily) via EventBridge
- Store in DynamoDB for fast retrieval with TTL for data freshness

#### 2. Historical Booking Data
**Current**: Static historical performance data
**Production Goal**: Live PMS integration for real booking data
**AgentCore Gateway Integration**:
- Connect to Property Management Systems (Opera, Protel, RMS)
- Create Lambda function to extract and transform booking data
- Implement data pipeline with Kinesis for real-time streaming
- Store in Amazon Timestream for time-series analysis

#### 3. Local Events Data
**Current**: Static events calendar
**Production Goal**: Dynamic event feeds and impact analysis
**AgentCore Gateway Integration**:
- Connect to event calendar APIs (Eventbrite, local tourism boards)
- Create Lambda function to analyze event impact on demand
- Integrate with social media APIs for sentiment analysis
- Use SageMaker for predictive event impact modeling

#### 4. Revenue Management Best Practices
**Current**: Static industry guidelines
**Production Goal**: Dynamic benchmarking and personalized recommendations
**AgentCore Gateway Integration**:
- Connect to industry benchmark APIs (STR, Tourism Economics)
- Create Lambda function to generate personalized best practices
- Integrate with machine learning models for adaptive recommendations
- Use Amazon Personalize for customized strategy suggestions

### Implementation Architecture

```
AgentCore Gateway
├── Competitor Data Service (Lambda + API Gateway)
│   ├── RateGain API Integration
│   ├── OTA Insight API Integration
│   └── DynamoDB Storage
├── Booking Data Service (Lambda + Kinesis)
│   ├── PMS Integration (Opera/Protel)
│   ├── Real-time Data Streaming
│   └── Timestream Storage
├── Events Data Service (Lambda + EventBridge)
│   ├── Event Calendar APIs
│   ├── Social Media Integration
│   └── SageMaker ML Models
└── Benchmarking Service (Lambda + S3)
    ├── STR API Integration
    ├── Industry Data Processing
    └── Personalize Recommendations
```

### Migration Strategy

1. **Phase 1**: Keep current knowledge base as fallback
2. **Phase 2**: Implement one data source at a time via AgentCore Gateway
3. **Phase 3**: Add intelligent caching and error handling
4. **Phase 4**: Remove static files once all integrations are stable

### Benefits of Production Integration

- **Real-time Data**: Always current market conditions and competitor rates
- **Scalability**: Handle multiple properties and markets simultaneously  
- **Accuracy**: Eliminate manual data updates and human errors
- **Intelligence**: ML-powered insights and predictive analytics
- **Compliance**: Secure data handling and audit trails via AWS services
