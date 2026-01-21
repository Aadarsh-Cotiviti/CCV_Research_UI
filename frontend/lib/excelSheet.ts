import fs from "fs/promises";
import path from "path";
import * as XLSX from "xlsx";

export type ExcelJsonSyncResult = {
  excelPath: string;
  jsonPath: string;
  updated: boolean;
  data: Record<string, unknown>[];
};

const dataDir = path.join(process.cwd(), "data");
const EXCEL_FILE_NAMES = ["CPT Codes with descriptions.xlsx"] as const;

/**
 * Synchronizes all .xlsx files in /data into sibling .json files.
 * A JSON file is (re)generated when missing or older than the Excel source.
 */
export async function ensureExcelJsonFiles(): Promise<ExcelJsonSyncResult[]> {
  const excelFiles = await listExcelFiles();
  const results: ExcelJsonSyncResult[] = [];

  for (const excelPath of excelFiles) {
    const jsonPath = getJsonPath(excelPath);
    const shouldRefresh = await needsRegeneration(excelPath, jsonPath);
    let data: Record<string, unknown>[];

    if (shouldRefresh) {
      data = await convertExcelToJson(excelPath, jsonPath);
    } else {
      const raw = await fs.readFile(jsonPath, "utf8");
      data = JSON.parse(raw) as Record<string, unknown>[];
    }

    results.push({ excelPath, jsonPath, updated: shouldRefresh, data });
  }
  return results;
}

async function listExcelFiles(): Promise<string[]> {
  const candidates = EXCEL_FILE_NAMES.map((file) => path.join(dataDir, file));
  const existing: string[] = [];

  for (const filePath of candidates) {
    if (await fileExists(filePath)) existing.push(filePath);
  }

  return existing;
}

function getJsonPath(excelPath: string): string {
  const base = path.basename(excelPath, path.extname(excelPath));
  return path.join(path.dirname(excelPath), `${base}.json`);
}

async function needsRegeneration(excelPath: string, jsonPath: string): Promise<boolean> {
  try {
    const [excelStat, jsonStat] = await Promise.all([fs.stat(excelPath), fs.stat(jsonPath)]);
    return excelStat.mtimeMs > jsonStat.mtimeMs;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return true;
    }

    throw error;
  }
}

async function convertExcelToJson(
  excelPath: string,
  jsonPath: string
): Promise<Record<string, unknown>[]> {
  const buffer = await fs.readFile(excelPath);
  const workbook = XLSX.read(buffer, { type: "buffer", cellDates: true });
  const sheetName = workbook.SheetNames[0];

  if (!sheetName) {
    await writeJson(jsonPath, []);
    return [];
  }

  const sheet = workbook.Sheets[sheetName];

  const data = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, {
    defval: "",
    raw: true,
    blankrows: false,
  });

  // Drop rows that are entirely empty after conversion
  const filtered = data.filter((row) =>
    Object.values(row).some((value) => value !== "" && value !== null && value !== undefined)
  );

  await writeJson(jsonPath, filtered);
  return filtered;
}

async function writeJson(jsonPath: string, data: unknown[]): Promise<void> {
  await fs.mkdir(path.dirname(jsonPath), { recursive: true });
  await fs.writeFile(jsonPath, JSON.stringify(data, null, 2), "utf8");
}

async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}
