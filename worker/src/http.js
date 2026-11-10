/** JSON responses and CORS headers for the website's origin. */
export class Http {
  static MAX_BODY = 4096;

  /** The CORS headers for this request, or {} when its origin isn't allowed. */
  static cors(request, allowedOrigins) {
    const origin = request.headers.get("Origin");
    if (!origin || !allowedOrigins.includes(origin)) return {};
    return {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
      "Access-Control-Max-Age": "86400",
      Vary: "Origin",
    };
  }

  static json(data, status = 200, headers = {}) {
    return new Response(JSON.stringify(data), {
      status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...headers },
    });
  }

  /** The request body as an object; rejects bodies that are too big or not JSON objects. */
  static async body(request) {
    const text = await request.text();
    if (text.length > Http.MAX_BODY) return null;
    try {
      const data = JSON.parse(text);
      return data && typeof data === "object" && !Array.isArray(data) ? data : null;
    } catch {
      return null;
    }
  }

  /** The token from "Authorization: Bearer <token>", or null. */
  static bearer(request) {
    const m = /^Bearer\s+(\S+)$/.exec(request.headers.get("Authorization") || "");
    return m ? m[1] : null;
  }
}
