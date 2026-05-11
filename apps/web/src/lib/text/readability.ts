/**
 * Flesch-Kincaid Grade Level readability helper (T-AMD-18, FR-039).
 *
 * Inline implementation — no external library dependency (reuse-only constraint).
 * Formula: FKGL = 0.39 × (words/sentences) + 11.8 × (syllables/words) − 15.59
 *
 * Returns a grade-level number; ≤ 8.0 is the plain-language target for
 * public information content (SC-015).
 */

/** Count syllables in an English word using heuristic vowel-cluster counting. */
export function countSyllables(word: string): number {
  const cleaned = word.toLowerCase().replace(/[^a-z]/g, "");
  if (cleaned.length === 0) return 0;
  if (cleaned.length <= 3) return 1;

  // Remove trailing silent e
  const w = cleaned.replace(/e$/, "");
  // Count vowel clusters (sequences of vowels = one syllable each)
  const matches = w.match(/[aeiouy]+/g);
  const count = matches ? matches.length : 1;
  return Math.max(1, count);
}

/** Count sentences in a text block (split on . ! ? terminators). */
export function countSentences(text: string): number {
  const matches = text.match(/[.!?]+/g);
  return Math.max(1, matches ? matches.length : 1);
}

/** Count words (whitespace-separated tokens of ≥1 alpha char). */
export function countWords(text: string): number {
  const tokens = text.trim().split(/\s+/).filter((t) => /[a-zA-Z]/.test(t));
  return Math.max(1, tokens.length);
}

/**
 * Flesch-Kincaid Grade Level.
 *
 * @param text - Plain English text to analyse.
 * @returns Grade level (e.g. 8.0 = Year 8 reading difficulty).
 */
export function fleschKincaidGradeLevel(text: string): number {
  const words = countWords(text);
  const sentences = countSentences(text);
  const tokens = text.trim().split(/\s+/).filter((t) => /[a-zA-Z]/.test(t));
  const syllables = tokens.reduce((sum, t) => sum + countSyllables(t), 0);

  const asl = words / sentences; // average sentence length
  const asw = syllables / words; // average syllables per word

  return 0.39 * asl + 11.8 * asw - 15.59;
}
