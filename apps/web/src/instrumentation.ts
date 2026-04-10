export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { useAzureMonitor } = await import("@azure/monitor-opentelemetry");
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useAzureMonitor({
      azureMonitorExporterOptions: {
        connectionString:
          process.env.APPLICATIONINSIGHTS_CONNECTION_STRING,
      },
    });
  }
}
