# Dynamic Report Template Generation with Conversational Interface

This document explains how to use the chat-based dynamic template generation functionality for creating custom reports.

## Overview

The dynamic template generation feature allows users to:

1. Have a conversation with an AI assistant to design report templates
2. Suggest appropriate report templates based on a query and available sources
3. Create and refine templates through an interactive chat interface
4. Generate reports using these templates with content from uploaded documents

## API Endpoints

### Template Management

- **GET /templates/list** - List all available templates
- **POST /templates/create** - Create a new custom template
- **PUT /templates/{template_id}** - Update an existing template
- **DELETE /templates/{template_id}** - Delete a template

### Conversational Template Generation

- **POST /templates/chat** - Have a conversation about template design needs
- **POST /templates/suggest** - Get AI-generated template suggestions with conversational context

### Report Generation

- **POST /generate** - Generate a report using a template

## Example Usage Flow

### 1. Chat-Based Template Design

Start a conversation with the template assistant:

```json
POST /templates/chat
{
  "message": "I need to create a report about renewable energy"
}
```

Response:

```json
{
  "response": "I'd be happy to help you create a report about renewable energy. This is a fascinating and relevant topic! To create the most effective template, I'd like to understand a bit more about your specific focus and goals:\n\n1. Are you focusing on any particular types of renewable energy (solar, wind, hydroelectric, geothermal, etc.)?\n2. Is this report meant to be technical, policy-oriented, or for general audiences?\n3. Are you analyzing current implementation, future potential, or comparing with traditional energy sources?\n4. Do you have any specific sections you already know you want to include?\n\nOnce I understand your needs better, I can suggest a tailored structure for your report.",
  "chat_history": [
    {
      "role": "user",
      "content": "I need to create a report about renewable energy"
    },
    {
      "role": "assistant",
      "content": "I'd be happy to help you create a report about renewable energy..."
    }
  ]
}
```

Continue the conversation:

```json
POST /templates/chat
{
  "message": "I want to focus on solar and wind energy for a business audience",
  "chat_history": [previous chat history array]
}
```

### 2. Dynamic Template Suggestion with Chat Context

After discussing your needs in the chat, you can request a concrete template:

```json
POST /templates/suggest
{
  "query": "Business analysis of solar and wind energy implementation",
  "source_id": "optional_specific_source",
  "context": {
    "sources": [
      {"source_id": "energy_docs", "count": 3},
      {"source_id": "policy_papers", "count": 2}
    ]
  },
  "chat_history": [array of previous chat messages]
}
```

Response:

```json
{
  "status": "created",
  "template": {
    "id": "c88f9e3d-8a7b-4e9a-b236-53cf73dad0ff",
    "template": [
      "Executive Summary",
      "Market Overview of Solar and Wind Technologies",
      "Investment Analysis and ROI Projections",
      "Operational Considerations",
      "Regulatory Environment and Incentives",
      "Competitive Landscape",
      "Strategic Recommendations"
    ],
    "query": "Business analysis of solar and wind energy implementation",
    "source_based": true
  },
  "conversation": "Based on our discussion about creating a business-focused report on solar and wind energy, I've designed a template that addresses the key aspects business leaders would want to see...",
  "message": "Created template with 7 sections based on your query."
}
```

### 2. Generate Report Using Template

Once you have a suggested template, you can generate a report using it:

```json
POST /generate
{
  "template_id": "c88f9e3d-8a7b-4e9a-b236-53cf73dad0ff",
  "query": "Benefits of renewable energy in the power grid",
  "source_filter": "energy_docs"
}
```

### 3. Creating Custom Templates

You can also create custom templates:

```json
POST /templates/create
{
  "template": [
    "Executive Summary",
    "Market Analysis",
    "Competitive Landscape",
    "SWOT Analysis",
    "Strategic Recommendations"
  ],
  "name": "Business Strategy Template"
}
```

## Implementation Details

The dynamic template suggestion feature uses:

1. Google's Gemini AI model to analyze the query and context
2. Source document metadata to refine suggestions based on available content
3. Modular template storage for easy reuse and management

## Best Practices

1. **Start with a conversation** - Begin by chatting with the assistant about your report needs
2. **Provide specific details** - The more context you share, the more tailored your template will be
3. **Iterate through discussion** - Refine the template ideas through back-and-forth conversation
4. **Provide source context** - When available, filtering by specific sources makes reports more focused
5. **Review and customize** - You can edit suggested templates before generating reports
6. **Save useful templates** - Templates that work well can be saved for future use

## Web 4.0 Conversational Experience

The chat-based template generation represents a shift toward a Web 4.0 approach where:

1. **Contextual Understanding** - The system remembers previous interactions and builds on them
2. **Natural Conversation** - Users interact with the system through natural language dialog
3. **Personalization** - Templates are tailored to specific user needs through conversation
4. **Collaborative Creation** - The user and AI assistant work together to design the best template
5. **Iterative Refinement** - Templates evolve through conversation rather than one-shot generation
