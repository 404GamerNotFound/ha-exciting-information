/* eslint-disable no-underscore-dangle */
const LitElement = window.LitElement || Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
const html = window.html || LitElement.prototype.html;
const css = window.css || LitElement.prototype.css;

class PVExcitingInformationCard extends LitElement {
  static get properties() {
    return {
      hass: {},
      _config: { state: true },
      _index: { state: true },
    };
  }

  setConfig(config) {
    if (!config || !config.entities || !Array.isArray(config.entities)) {
      throw new Error("You need to define an entities array");
    }

    this._config = {
      title: config.title || "PV Exciting Information",
      show_controls: config.show_controls !== false,
      entities: config.entities,
    };
    this._index = 0;
  }

  getCardSize() {
    return 3;
  }

  _handlePrev() {
    const entities = this._config.entities;
    this._index = (this._index - 1 + entities.length) % entities.length;
  }

  _handleNext() {
    const entities = this._config.entities;
    this._index = (this._index + 1) % entities.length;
  }

  _setIndex(index) {
    this._index = index;
  }

  _normalizeEntity(entry) {
    if (typeof entry === "string") {
      return { entity: entry };
    }
    return entry;
  }

  _getStateValue(stateObj, entry) {
    if (!stateObj) {
      return { value: "—", unit: "" };
    }

    if (entry.attribute) {
      const attrValue = stateObj.attributes[entry.attribute];
      return { value: attrValue ?? "—", unit: entry.unit || "" };
    }

    return {
      value: stateObj.state,
      unit: stateObj.attributes.unit_of_measurement || "",
    };
  }

  _getSecondaryText(stateObj, entry) {
    if (!stateObj) {
      return "";
    }

    if (entry.secondary_attribute) {
      const attrValue = stateObj.attributes[entry.secondary_attribute];
      return attrValue ?? "";
    }

    return entry.secondary || "";
  }

  render() {
    if (!this.hass || !this._config) {
      return html``;
    }

    const entities = this._config.entities.map((entry) => this._normalizeEntity(entry));
    if (entities.length === 0) {
      return html`
        <ha-card>
          <div class="empty">No entities configured</div>
        </ha-card>
      `;
    }

    const active = entities[this._index % entities.length];
    const stateObj = this.hass.states[active.entity];
    const title = active.name || stateObj?.attributes.friendly_name || active.entity;
    const icon = active.icon || stateObj?.attributes.icon || "mdi:solar-power";
    const { value, unit } = this._getStateValue(stateObj, active);
    const secondary = this._getSecondaryText(stateObj, active);

    return html`
      <ha-card>
        ${this._config.title
          ? html`<div class="card-header">${this._config.title}</div>`
          : ""}
        <div class="slider">
          <div class="slide">
            <div class="slide-header">
              <ha-icon class="slide-icon" .icon=${icon}></ha-icon>
              <div class="slide-title">${title}</div>
            </div>
            <div class="slide-value">
              <span class="value">${value}</span>
              ${unit ? html`<span class="unit">${unit}</span>` : ""}
            </div>
            ${secondary ? html`<div class="slide-secondary">${secondary}</div>` : ""}
          </div>
        </div>
        ${this._config.show_controls
          ? html`
              <div class="controls">
                <ha-icon-button
                  .label=${this.hass.localize("ui.common.previous") || "Previous"}
                  .icon=${"mdi:chevron-left"}
                  @click=${this._handlePrev}
                ></ha-icon-button>
                <div class="dots">
                  ${entities.map(
                    (_entry, index) => html`
                      <button
                        class=${index === this._index ? "dot active" : "dot"}
                        @click=${() => this._setIndex(index)}
                        aria-label="Go to slide ${index + 1}"
                      ></button>
                    `,
                  )}
                </div>
                <ha-icon-button
                  .label=${this.hass.localize("ui.common.next") || "Next"}
                  .icon=${"mdi:chevron-right"}
                  @click=${this._handleNext}
                ></ha-icon-button>
              </div>
            `
          : ""}
      </ha-card>
    `;
  }

  static get styles() {
    return css`
      ha-card {
        padding: 16px;
      }

      .card-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 12px;
      }

      .slider {
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .slide {
        width: 100%;
        text-align: center;
      }

      .slide-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-bottom: 8px;
      }

      .slide-icon {
        color: var(--secondary-text-color);
      }

      .slide-title {
        font-weight: 600;
      }

      .slide-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-text-color);
      }

      .unit {
        margin-left: 6px;
        font-size: 1rem;
        color: var(--secondary-text-color);
      }

      .slide-secondary {
        margin-top: 6px;
        color: var(--secondary-text-color);
      }

      .controls {
        margin-top: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
      }

      .dots {
        display: flex;
        gap: 6px;
      }

      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        border: 0;
        background: var(--disabled-text-color);
        cursor: pointer;
      }

      .dot.active {
        background: var(--primary-color);
      }

      .empty {
        padding: 16px;
        text-align: center;
        color: var(--secondary-text-color);
      }
    `;
  }
}

customElements.define("pv-exciting-information-card", PVExcitingInformationCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "pv-exciting-information-card",
  name: "PV Exciting Information Card",
  description: "Slider card for PV Exciting Information sensors.",
});
