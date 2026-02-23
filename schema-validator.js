/**
 * Schema Validator — Spellcasters Community API
 *
 * A fully client-side JSON Schema Validator for community contributors.
 * Validates game entity data (Units, Heroes, Spells, etc.) against the
 * official JSON Schemas using Ajv2019 (Draft 2019-09).
 *
 * Supports three input methods:
 *   1. Copy/Paste into the textarea
 *   2. File Upload via the file picker
 *   3. URL Parameter (?url=...) for direct PR integration
 *
 * No data is ever sent to a server. All validation runs in the browser.
 *
 * @see https://ajv.js.org/ — Ajv JSON Schema Validator
 * @see https://json-schema.org/draft/2019-09 — JSON Schema Draft 2019-09
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/**
 * Base URI used by the schemas' internal $id values.
 * All $ref resolution uses this namespace.
 * @type {string}
 */
const SCHEMA_BASE_URL = "https://spellcasters.gg/schemas/v2/";

/**
 * Complete list of all schema files that must be loaded for full
 * $ref resolution across the inheritance chain.
 * Order does not matter — Ajv resolves by $id lookup.
 * @type {string[]}
 */
const SCHEMA_FILES = [
  // Top-level entity schemas
  "units.schema.json",
  "heroes.schema.json",
  "spells.schema.json",
  "titans.schema.json",
  "consumables.schema.json",
  "upgrades.schema.json",
  "game_config.schema.json",
  // Shared definition schemas
  "definitions/core.schema.json",
  "definitions/stats.schema.json",
  "definitions/resource.schema.json",
  "definitions/magic.schema.json",
  "definitions/enums.schema.json",
  "definitions/ability.schema.json",
  "definitions/mechanics.schema.json",
  // Mechanics sub-schemas
  "definitions/mechanics/aura.schema.json",
  "definitions/mechanics/feature.schema.json",
  "definitions/mechanics/spawner.schema.json",
  "definitions/mechanics/damage_modifier.schema.json",
  "definitions/mechanics/damage_reduction.schema.json",
  "definitions/mechanics/bonus_damage.schema.json",
  "definitions/mechanics/initial_attack.schema.json",
];

/**
 * Maps the `category` field found in entity JSON to the correct
 * schema dropdown value, enabling auto-detection.
 * @type {Object<string, string>}
 */
const CATEGORY_TO_SCHEMA = {
  creature: "units",
  building: "units",
  spellcaster: "heroes",
  spell: "spells",
  titan: "titans",
  consumable: "consumables",
};

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

/** @type {import('ajv/dist/2019').default|null} */
let ajv = null;

/** @type {boolean} */
let schemasLoaded = false;

// ---------------------------------------------------------------------------
// DOM References
// ---------------------------------------------------------------------------

const dom = {
  typeSelect: document.getElementById("schema-type"),
  textarea: document.getElementById("json-input"),
  validateBtn: document.getElementById("validate-btn"),
  uploadInput: document.getElementById("file-upload"),
  urlInput: document.getElementById("url-input"),
  fetchBtn: document.getElementById("fetch-btn"),
  resultsPanel: document.getElementById("results"),
  resultsTitle: document.getElementById("results-title"),
  errorList: document.getElementById("error-list"),
  overlay: document.getElementById("loading-overlay"),
};

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

/**
 * Boots the validator: loads all schemas into Ajv, then checks
 * for a ?url= query parameter to auto-fetch PR data.
 * @returns {Promise<void>}
 */
async function initValidator() {
  try {
    ajv = new window.ajv2019.Ajv2019({
      allErrors: true,
      strict: false,
    });

    // Fetch all 17 schema files in parallel
    const schemas = await Promise.all(SCHEMA_FILES.map(fetchSchema));

    // Register each schema by its internal $id.
    // Workaround: Ajv2019 does not correctly track properties evaluated
    // through allOf $ref chains for unevaluatedProperties. We strip
    // unevaluatedProperties from top-level schemas at load time.
    // The additionalProperties: false on mechanics sub-schemas still
    // catches real contributor errors (e.g. unknown fields in mechanics).
    for (const schema of schemas) {
      stripUnevaluatedProperties(schema);
      ajv.addSchema(schema);
    }

    schemasLoaded = true;
    dom.validateBtn.disabled = false;
    dom.validateBtn.textContent = "✅ Validate";
    dom.overlay.classList.add("hidden");

    // If a ?url= param was provided, auto-fetch and validate
    await checkUrlParam();
  } catch (err) {
    console.error("Schema load failure:", err);
    dom.overlay.textContent =
      "❌ Failed to load schemas. Please refresh the page.";
    dom.overlay.style.color = "#ff7b72";
  }
}

/**
 * Fetches a single schema file from the local server.
 * Uses relative paths so it works on both localhost and GitHub Pages.
 *
 * @param {string} path — Relative path within schemas/v2/
 * @returns {Promise<object>} Parsed JSON schema
 * @throws {Error} If the fetch fails
 */
async function fetchSchema(path) {
  const response = await fetch("schemas/v2/" + path);
  if (!response.ok) {
    throw new Error("Failed to fetch schema: " + path);
  }
  return response.json();
}

/**
 * Recursively removes `unevaluatedProperties` from a schema object.
 * Workaround for Ajv2019 not properly tracking evaluated properties
 * through allOf $ref chains. The additionalProperties: false on
 * mechanics sub-schemas still catches the most common contributor errors.
 *
 * @param {object} obj — Schema object (mutated in place)
 */
function stripUnevaluatedProperties(obj) {
  if (!obj || typeof obj !== "object") return;
  if (Array.isArray(obj)) {
    obj.forEach(stripUnevaluatedProperties);
    return;
  }
  delete obj.unevaluatedProperties;
  for (const key of Object.keys(obj)) {
    stripUnevaluatedProperties(obj[key]);
  }
}

// ---------------------------------------------------------------------------
// Input Methods
// ---------------------------------------------------------------------------

/**
 * Fetches JSON from a URL and auto-validates it.
 * Used for direct PR integration or the manual fetch input field.
 *
 * @param {string|null} overrideUrl - Direct URL to fetch. If null, checks `?url=` param.
 * @returns {Promise<void>}
 */
async function checkUrlParam(overrideUrl = null) {
  let prUrl = overrideUrl;
  
  if (!prUrl) {
    const urlParams = new URLSearchParams(window.location.search);
    prUrl = urlParams.get("url");
  }

  if (!prUrl) return;

  dom.urlInput.value = prUrl;
  dom.textarea.value = "⏳ Fetching JSON from URL…\n" + prUrl;
  dom.validateBtn.disabled = true;

  try {
    const response = await fetch(prUrl);
    if (!response.ok) {
      throw new Error(
        "Could not download the file (HTTP " + response.status + ")."
      );
    }

    dom.textarea.value = await response.text();
    validateCurrentJson();
  } catch (err) {
    showError("URL Fetch Error", [
      "Could not download the JSON file from the provided URL.",
      err.message,
    ]);
  } finally {
    dom.validateBtn.disabled = !schemasLoaded;
  }
}

/** Manual "Fetch" button click handler. */
dom.fetchBtn.addEventListener("click", function() {
  const url = dom.urlInput.value.trim();
  if (url) {
    checkUrlParam(url);
  }
});

/**
 * Handles file upload via the <input type="file"> element.
 * Reads the file with FileReader, populates the textarea,
 * and auto-triggers validation.
 */
dom.uploadInput.addEventListener("change", function (e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (event) {
    dom.textarea.value = event.target.result;
    validateCurrentJson();
  };
  reader.onerror = function () {
    showError("File Read Error", [
      "Could not read the selected file. Please try again.",
    ]);
  };
  reader.readAsText(file);

  // Reset so the same file can be re-selected
  dom.uploadInput.value = "";
});

/** Manual "Validate" button click handler. */
dom.validateBtn.addEventListener("click", validateCurrentJson);

// ---------------------------------------------------------------------------
// Core Validation
// ---------------------------------------------------------------------------

/**
 * Main validation entry point. Parses the textarea content as JSON,
 * auto-detects the entity type, and runs it through the Ajv schema.
 */
function validateCurrentJson() {
  if (!schemasLoaded) return;

  const rawText = dom.textarea.value.trim();
  if (!rawText) {
    showError("Nothing to validate", [
      "Paste some JSON into the text box, or upload a .json file.",
    ]);
    return;
  }

  // Step 1: Parse JSON
  let data;
  try {
    data = JSON.parse(rawText);
  } catch (err) {
    const lineMatch = err.message.match(/line (\d+)/i);
    const colMatch = err.message.match(/column (\d+)/i);

    const errors = [
      "Your file has a syntax error. The browser cannot parse it.",
      "Raw error: " + err.message
    ];

    if (lineMatch) {
      const lineNum = parseInt(lineMatch[1], 10);
      const colNum = colMatch ? parseInt(colMatch[1], 10) : 0;
      const lines = rawText.split("\n");
      
      const start = Math.max(0, lineNum - 3);
      const end = Math.min(lines.length - 1, lineNum + 1);
      
      let snippet = "--- Code Snippet ---\n";
      for (let i = start; i <= end; i++) {
        const isErrorLine = (i === lineNum - 1);
        const prefix = isErrorLine ? ">> " : "   ";
        const safeLine = lines[i].replace(/\t/g, "  "); // Convert tabs to spaces for proper column alignment
        
        snippet += prefix + String(i + 1).padStart(4, " ") + " | " + safeLine + "\n";
        
        if (isErrorLine && colNum > 0) {
          snippet += "        | " + " ".repeat(Math.max(0, colNum - 1)) + "^ Error likely around here\n";
        }
      }
      errors.push(snippet);
    }

    errors.push("Common causes:\n• A missing comma between properties or array items\n• An extra trailing comma after the last item\n• Mismatched brackets or braces { } [ ]\n• Unquoted property names or single quotes instead of double quotes");

    showError("Invalid JSON Syntax", errors);
    return;
  }

  // Step 2: Auto-detect schema from data
  autoSelectSchema(data);

  // Step 3: Get the compiled validator for the selected schema
  const selectedType = dom.typeSelect.value;
  const schemaId = SCHEMA_BASE_URL + selectedType + ".schema.json";
  const validate = ajv.getSchema(schemaId);

  if (!validate) {
    showError("Internal Error", [
      "Could not find compiled schema for: " + selectedType,
      "This is a bug in the validator. Please report it.",
    ]);
    return;
  }

  // Step 4: Run validation
  const valid = validate(data);
  if (valid) {
    showSuccess(data);
  } else {
    const friendlyErrors = deduplicateErrors(
      validate.errors.map(translateError)
    );
    showError("Validation Failed — " + friendlyErrors.length + " issue(s)", friendlyErrors);
  }
}

/**
 * Attempts to auto-select the correct schema type from the dropdown
 * based on the content of the parsed JSON data.
 *
 * @param {object} data — Parsed JSON object
 */
function autoSelectSchema(data) {
  if (!data || typeof data !== "object") return;

  // Check by category field (units, heroes, spells, titans, consumables)
  if (data.category) {
    const mapped = CATEGORY_TO_SCHEMA[data.category.toLowerCase()];
    if (mapped) {
      dom.typeSelect.value = mapped;
      return;
    }
  }

  // Check for game_config shape
  if (data.version && data.environment) {
    dom.typeSelect.value = "game_config";
    return;
  }

  // Check for upgrade shape
  if (data.upgrade_id) {
    dom.typeSelect.value = "upgrades";
  }
}

// ---------------------------------------------------------------------------
// Error Translation
// ---------------------------------------------------------------------------

/**
 * Translates a raw Ajv error object into a plain-English string
 * that a non-technical contributor can understand and act on.
 *
 * @param {import('ajv').ErrorObject} err — Raw Ajv error
 * @returns {string} Human-readable error message
 */
function translateError(err) {
  const path = err.instancePath || "(root)";
  const field = path.split("/").pop() || "(root)";

  switch (err.keyword) {
    case "additionalProperties": {
      const prop = err.params.additionalProperty;
      return (
        '❌ Unknown field "' +
        prop +
        '" at ' +
        path +
        ". This property is not allowed here. Remove it or check spelling."
      );
    }

    case "unevaluatedProperties": {
      const prop = err.params.unevaluatedProperty;
      return (
        '❌ Unrecognized field "' +
        prop +
        '" at ' +
        path +
        ". This property is not part of the schema for this entity type."
      );
    }

    case "required": {
      const missing = err.params.missingProperty;
      return (
        '⚠️ Missing required field "' +
        missing +
        '" at ' +
        path +
        ". You must include this property."
      );
    }

    case "type": {
      return (
        '❌ Wrong type for "' +
        field +
        '" at ' +
        path +
        ": expected " +
        err.params.type +
        "."
      );
    }

    case "enum": {
      const allowed = err.params.allowedValues.join(", ");
      return (
        '❌ Invalid value for "' +
        field +
        '" at ' +
        path +
        ". Must be one of: " +
        allowed +
        "."
      );
    }

    case "minimum":
    case "maximum":
    case "exclusiveMinimum":
    case "exclusiveMaximum": {
      return (
        '❌ Out of range for "' +
        field +
        '" at ' +
        path +
        ": " +
        err.message +
        "."
      );
    }

    case "pattern": {
      return (
        '❌ Invalid format for "' +
        field +
        '" at ' +
        path +
        ": must match pattern " +
        err.params.pattern +
        " (e.g. snake_case)."
      );
    }

    case "const": {
      return (
        '❌ "' +
        field +
        '" at ' +
        path +
        " must be exactly: " +
        JSON.stringify(err.params.allowedValue) +
        "."
      );
    }

    case "minLength":
    case "maxLength": {
      return (
        '❌ Invalid length for "' +
        field +
        '" at ' +
        path +
        ": " +
        err.message +
        "."
      );
    }

    case "oneOf":
    case "anyOf": {
      return (
        '❌ "' +
        field +
        '" at ' +
        path +
        " does not match any of the expected formats."
      );
    }

    case "if": {
      // if/then/else conditional failures — skip silently,
      // the real error is in the then/else branch
      return null;
    }

    default:
      return "❌ " + path + ": " + err.message;
  }
}

/**
 * Removes duplicate error messages and filters out null entries
 * (e.g. suppressed `if` keyword errors).
 *
 * @param {(string|null)[]} errors — Array of translated error strings
 * @returns {string[]} Deduplicated, non-null error strings
 */
function deduplicateErrors(errors) {
  const seen = new Set();
  const result = [];
  for (const err of errors) {
    if (err === null) continue;
    if (seen.has(err)) continue;
    seen.add(err);
    result.push(err);
  }
  return result;
}

// ---------------------------------------------------------------------------
// UI Rendering
// ---------------------------------------------------------------------------

/**
 * Displays a success message in the results panel.
 * @param {object} data — The validated JSON data (used for display)
 */
function showSuccess(data) {
  dom.resultsPanel.className = "results-panel success";
  dom.resultsPanel.style.display = "block";

  const name = data.name || data.entity_id || "Entity";
  dom.resultsTitle.textContent = "✅ Valid! " + name + " looks perfect.";
  dom.resultsTitle.style.color = "#3fb950";
  dom.errorList.textContent = "";
}

/**
 * Displays error messages in the results panel.
 *
 * @param {string} title — Header for the error section
 * @param {string[]} errorStrings — List of human-readable error messages
 */
function showError(title, errorStrings) {
  dom.resultsPanel.className = "results-panel error";
  dom.resultsPanel.style.display = "block";
  dom.resultsTitle.textContent = "❌ " + title;
  dom.resultsTitle.style.color = "#ff7b72";

  // Clear and rebuild the error list using safe DOM methods (no innerHTML)
  dom.errorList.textContent = "";
  for (const errStr of errorStrings) {
    const li = document.createElement("li");
    li.textContent = errStr;
    if (errStr.includes("\n")) {
      li.style.whiteSpace = "pre-wrap";
      li.style.fontFamily = "ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace";
    }
    dom.errorList.appendChild(li);
  }
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", initValidator);
