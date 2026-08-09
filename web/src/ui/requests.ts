import { z } from "zod";
import { requestSchema } from "../contract";

/** The requests backlog panel behind `?crlf=1`. */
export class RequestsPanel {
  private panel: HTMLElement;
  private requests: z.infer<typeof requestSchema>[] = [];
  private visible = false;

  constructor() {
    this.panel = document.createElement("div");
    this.panel.id = "requests-panel";
    this.panel.className = "hud-panel";
    this.panel.hidden = true;
    document.getElementById("app")!.appendChild(this.panel);
  }

  async load(url: string): Promise<boolean> {
    try {
      const response = await fetch(url);
      if (!response.ok) return false;
      this.requests = z.array(requestSchema).parse(await response.json());
      this.render();
      return true;
    } catch {
      return false;
    }
  }

  toggle(): void {
    this.visible = !this.visible;
    this.panel.hidden = !this.visible;
  }

  private render(): void {
    // Sort worst-first: CRITICAL -> LOW
    const priorityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
    const sorted = [...this.requests].sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

    this.panel.innerHTML = `
      <div class="panel-header">
        <b>Data Requests</b>
        <span class="provenance">SIMULATED</span>
      </div>
      <table>
        ${sorted
          .map(
            (r) => `
          <tr>
            <td><span class="badge ${r.priority.toLowerCase()}">${r.priority}</span></td>
            <td>${r.description}</td>
            <td>${r.status}</td>
          </tr>`
          )
          .join("")}
      </table>
    `;
  }
}
