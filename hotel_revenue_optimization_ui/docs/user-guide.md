# Hotel Revenue Optimization UI - User Guide

This guide provides instructions on how to use the Hotel Revenue Optimization UI to get AI-powered recommendations for optimizing your hotel's revenue.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Natural Language Interface](#natural-language-interface)
4. [Structured Form Interface](#structured-form-interface)
5. [Understanding Results](#understanding-results)
6. [Query History](#query-history)
7. [User Profile](#user-profile)
8. [Tips for Best Results](#tips-for-best-results)

## Getting Started

### Logging In

1. Navigate to the application URL provided by your administrator
2. Click the "Login" button in the top-right corner
3. Enter your email and password
4. If this is your first login, you'll be prompted to change your temporary password

### Navigation

The main navigation menu includes:

- **Home**: Landing page with overview information
- **Dashboard**: Main dashboard with quick actions and sample queries
- **Natural Language**: Interface for submitting free-form queries
- **Structured Form**: Interface for submitting structured queries with dropdown options
- **History**: View your previous queries and results
- **Help**: Access detailed help documentation
- **Profile**: View and manage your user profile (accessible from the dropdown in the top-right corner)

## Dashboard Overview

The dashboard provides a quick overview of the system and easy access to its main features:

- **Quick Actions**: Buttons to access the Natural Language interface, Structured Form interface, and Query History
- **Sample Queries**: Example queries to help you get started
- **How to Use This System**: Brief instructions on using both interfaces

## Natural Language Interface

The Natural Language interface allows you to ask questions or request recommendations in plain English:

1. Navigate to the Natural Language page from the dashboard or navigation menu
2. Type your query in the text box
3. Click "Submit Query"
4. Wait for the system to process your query (this may take a few moments)
5. Review the results displayed on the page

### Example Queries

- "Optimize pricing for a 4-star hotel in Miami during summer season"
- "Forecast demand for a business hotel in New York for next quarter"
- "Analyze competitor pricing for luxury hotels in San Francisco"
- "Recommend revenue strategy for a resort hotel during low season"
- "Calculate optimal room rates for weekend vs weekday stays"

### Tips for Effective Queries

- Be specific about your hotel type, location, and time period
- Mention your goals (maximize revenue, occupancy, etc.)
- Include any relevant constraints or considerations
- Use clear, concise language

## Structured Form Interface

The Structured Form interface provides a more guided experience with dropdown menus and input fields:

1. Navigate to the Structured Form page from the dashboard or navigation menu
2. Fill out the form with your hotel's information:
   - **Hotel Type**: Select your hotel category (luxury, business, resort, etc.)
   - **Location**: Enter your hotel's city, state, or region
   - **Season**: Select the current or upcoming season
   - **Star Rating**: Select your hotel's official star rating
   - **Current Occupancy Rate**: Enter your hotel's current occupancy percentage
   - **Include Competitor Analysis**: Check this box to include analysis of competitor pricing
   - **Optimization Goal**: Select your primary goal (maximize revenue, occupancy, profit, or balance)
3. Click "Generate Recommendations"
4. Wait for the system to process your request
5. Review the results displayed on the page

## Understanding Results

The results from both interfaces include:

### Markdown Content

The system generates a comprehensive report in Markdown format, which is rendered as formatted HTML. This report typically includes:

- **Executive Summary**: A brief overview of the key recommendations
- **Market Analysis**: Analysis of current market conditions and trends
- **Demand Forecast**: Predictions of future demand patterns
- **Pricing Recommendations**: Specific pricing strategies for different room types and time periods
- **Competitor Analysis**: Comparison with competitor pricing (if requested)
- **Implementation Plan**: Steps to implement the recommended strategies
- **Expected Outcomes**: Projected impact on revenue, occupancy, and profit

### Raw Result

Below the formatted report, you'll find the raw JSON result from the API. This includes all the data returned by the system and can be useful for technical users or for troubleshooting.

### Actions

- **Print**: Click the Print button to print the report or save it as a PDF
- **Run Again**: From the History page, you can run previous queries again

## Query History

The Query History page shows a list of your previous queries:

- **Date/Time**: When the query was submitted
- **Query**: The text of your query or a summary of your form inputs
- **Summary**: A brief summary of the results
- **Actions**: Options to run the query again or view the full results

## User Profile

The User Profile page shows your account information:

- **Name**: Your full name
- **Email**: Your email address
- **User ID**: Your unique identifier in the system

From this page, you can also:
- **Logout**: End your current session
- **Manage Account**: Access the Cognito User Portal to update your profile or change your password

## Tips for Best Results

### For Natural Language Queries

- **Be Specific**: Include details about your hotel type, location, star rating, and current situation
- **Define Goals**: Clearly state what you're trying to optimize (revenue, occupancy, profit)
- **Provide Context**: Mention relevant factors like seasonality, local events, or competitor activities
- **Ask Focused Questions**: Break complex questions into simpler, more focused queries

### For Structured Form

- **Complete All Fields**: Fill out all form fields for the most accurate recommendations
- **Be Accurate**: Provide accurate information, especially for occupancy rates and star rating
- **Consider Your Goal**: Select the optimization goal that best aligns with your business objectives
- **Include Competitor Analysis**: Enable this option to get insights on competitive positioning

### General Tips

- **Review Thoroughly**: Take time to read through all sections of the recommendations
- **Consider Implementation**: Focus on recommendations that are practical to implement
- **Track Results**: Use the system regularly and compare results over time
- **Iterate**: Refine your queries based on the quality of recommendations received
