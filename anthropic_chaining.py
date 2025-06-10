{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "I apologize for the confusion, but I don't have any previous context or output to reference. As an AI language model, I don't maintain a conversation history or memory of previous interactions. Each prompt or question is treated as a new and independent conversation.\n",
      "\n",
      "If there's something specific you'd like assistance with, please feel free to ask your question or provide more details about what you need help with. I'll do my best to provide a relevant and helpful response based on the information you give me.\n"
     ]
    }
   ],
   "source": [
    "import anthropic\n",
    "import os\n",
    "\n",
    "client = anthropic.Anthropic(api_key=os.getenv(\"ANTHROPIC_API_KEY\"))\n",
    "\n",
    "# Step 1: Initial prompt\n",
    "Pi\n",
    "initial_prompt = \"As a data engineer, review the following document processing pipeline setup for our enterprise document intelligence system. Evaluate specifically the implementation plan for parsing various formats (PDF, DOCX, TXT), chunking strategies, and preprocessing techniques. <pipeline_plan>{{PIPELINE_PLAN}}</pipeline_plan>\"\n",
    "response_1 = client.messages.create(\n",
    "    model=\"claude-3-opus-20240229\",\n",
    "    max_tokens=1024,\n",
    "    system = \"You are Claude, an expert AI assistant specializing in enterprise-grade Retrieval-Augmented Generation (RAG) solutions. Your role is to provide precise, detailed, and actionable analysis, recommendations, and evaluations for an Enterprise Document Intelligence System. Your tasks will involve evaluating technical strategies and architectures across several domains Always assess each provided strategy for clarity, scalability, security, cost-effectiveness, actionability, and alignment with enterprise priorities. Clearly articulate strengths, identify critical gaps or risks, and provide specific, step-by-step recommendations for improvement. Your responses should be professional, structured, and immediately actionable, using clear grading systems (e.g., A+, A-, B+) to highlight key insights and areas needing attention.\",\n",
    "    messages=[{\"role\": \"user\", \n",
    "        \"content\": initial_prompt}]\n",
    ")\n",
    "output_1 = response_1.content[0].text\n",
    "\n",
    "# Step 2: Use response from step 1 in next prompt\n",
    "second_prompt = f\"Next prompt using previous output: {output_1}\"\n",
    "response_2 = client.messages.create(\n",
    "    model=\"claude-3-opus-20240229\",\n",
    "    max_tokens=1024,\n",
    "    messages=[{\"role\": \"user\", \"content\": second_prompt}]\n",
    ")\n",
    "output_2 = response_2.content[0].text\n",
    "\n",
    "print(output_2)\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "dsc80",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.18"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
