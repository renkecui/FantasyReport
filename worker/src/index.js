// Cloudflare Worker entry point: every request goes to ApiWorker.
import { ApiWorker } from "./api-worker.js";

export default {
  fetch(request, env) {
    return new ApiWorker(env).handle(request);
  },
};
