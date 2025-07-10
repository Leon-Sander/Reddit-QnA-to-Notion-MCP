FROM python:3.12-slim

WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY reddit_qa_to_notion_mcp.py .

EXPOSE 8000
CMD ["uv", "run", "reddit_qa_to_notion_mcp.py", "--transport", "http"]