/** An error that becomes an HTTP response with this status and message. */
export class HttpError extends Error {
  constructor(status, message, extra = {}) {
    super(message);
    this.status = status;
    this.extra = extra;
  }
}
