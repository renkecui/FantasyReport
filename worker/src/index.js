// Cloudflare Worker entry point: every request goes to ApiWorker; the crons in wrangler.toml go to
// UpdateTrigger, which starts the league update on GitHub.
import { ApiWorker } from "./api-worker.js";
import { UpdateTrigger } from "./update-trigger.js";

export default {
  fetch(request, env) {
    return new ApiWorker(env).handle(request);
  },
  scheduled(controller, env, ctx) {
    ctx.waitUntil(new UpdateTrigger(env).run(new Date(controller.scheduledTime)));
  },
};
