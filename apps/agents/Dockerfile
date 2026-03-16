FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml ./
COPY common ./common
COPY monitoring ./monitoring
COPY risk_assessment ./risk_assessment
COPY evacuation ./evacuation
COPY resource_allocation ./resource_allocation
COPY communication ./communication
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

FROM python:3.12-slim AS runtime

RUN useradd -m -u 10001 appuser
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY common ./common
COPY monitoring ./monitoring
COPY risk_assessment ./risk_assessment
COPY evacuation ./evacuation
COPY resource_allocation ./resource_allocation
COPY communication ./communication

USER appuser
CMD ["python", "-m", "monitoring.agent"]
