export default async function handler(req, res) {
  const pythonHttpBase = process.env.PYTHON_HTTP_BASE || "http://127.0.0.1:5000";

  if (req.method !== "POST") {
    res.status(405).json({ error: "Only POST method is allowed" });
    return;
  }

  try {
    const flaskResponse = await fetch(`${pythonHttpBase}/api/stop`, {
      method: "POST",
    });

    const data = await flaskResponse.json();

    if (!flaskResponse.ok) {
      throw new Error(data.error || "Failed to stop service");
    }

    res.status(200).json(data);
  } catch (error) {
    console.error("Service stop error:", error);
    res.status(500).json({
      status: "error",
      error: error.message,
    });
  }
}
