export type BloodGroup = "A+" | "A-" | "B+" | "B-" | "AB+" | "AB-" | "O+" | "O-";

export interface PatientProfile {
  id: string;
  name: string;
  age: number;
  gender: "Male" | "Female";
  heightCm: number;
  weightKg: number;
}

export interface CompatibilityData {
  clinicalBadge: string;
  canReceiveRbcFrom: BloodGroup[];
  canDonateRbcTo: BloodGroup[];
  plasmaCanReceiveFrom: BloodGroup[];
  plasmaCanDonateTo: BloodGroup[];
  rarityInPopulation: string;
  emergencyUniversalStatus: string;
}

export const BLOOD_COMPATIBILITY: Record<BloodGroup, CompatibilityData> = {
  "O-": {
    clinicalBadge: "Universal Red Blood Cell (RBC) Donor",
    canReceiveRbcFrom: ["O-"],
    canDonateRbcTo: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    plasmaCanReceiveFrom: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    plasmaCanDonateTo: ["O-"],
    rarityInPopulation: "~7% Global (Critical Emergency Reserve)",
    emergencyUniversalStatus: "🚨 Standard Emergency Trauma Choice (Safe for all recipients prior to cross-matching)"
  },
  "O+": {
    clinicalBadge: "Universal Positive RBC Donor",
    canReceiveRbcFrom: ["O+", "O-"],
    canDonateRbcTo: ["O+", "A+", "B+", "AB+"],
    plasmaCanReceiveFrom: ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"],
    plasmaCanDonateTo: ["O+", "A+", "B+", "AB+"],
    rarityInPopulation: "~38% (Most Common Worldwide)",
    emergencyUniversalStatus: "Most widely transfused red cell unit in clinical hospital networks"
  },
  "A-": {
    clinicalBadge: "Rh-Negative A Donor",
    canReceiveRbcFrom: ["A-", "O-"],
    canDonateRbcTo: ["A+", "A-", "AB+", "AB-"],
    plasmaCanReceiveFrom: ["A-", "A+", "AB-", "AB+"],
    plasmaCanDonateTo: ["A-", "O-"],
    rarityInPopulation: "~6% Population",
    emergencyUniversalStatus: "High demand for negative-group trauma cases"
  },
  "A+": {
    clinicalBadge: "Standard A-Positive Profile",
    canReceiveRbcFrom: ["A+", "A-", "O+", "O-"],
    canDonateRbcTo: ["A+", "AB+"],
    plasmaCanReceiveFrom: ["A+", "AB+"],
    plasmaCanDonateTo: ["A+", "A-", "O+", "O-"],
    rarityInPopulation: "~34% Population",
    emergencyUniversalStatus: "Second most common recipient cohort in emergency triage"
  },
  "B-": {
    clinicalBadge: "Rh-Negative B Donor",
    canReceiveRbcFrom: ["B-", "O-"],
    canDonateRbcTo: ["B+", "B-", "AB+", "AB-"],
    plasmaCanReceiveFrom: ["B-", "B+", "AB-", "AB+"],
    plasmaCanDonateTo: ["B-", "O-"],
    rarityInPopulation: "~2% Population (Very Rare in Western Countries, 15% in South Asia)",
    emergencyUniversalStatus: "Priority matching required to prevent RhD isoimmunization"
  },
  "B+": {
    clinicalBadge: "Standard B-Positive Profile",
    canReceiveRbcFrom: ["B+", "B-", "O+", "O-"],
    canDonateRbcTo: ["B+", "AB+"],
    plasmaCanReceiveFrom: ["B+", "AB+"],
    plasmaCanDonateTo: ["B+", "B-", "O+", "O-"],
    rarityInPopulation: "~9% Globally (High Prevalence in Asia)",
    emergencyUniversalStatus: "Key focus for voluntary whole blood and platelet apheresis"
  },
  "AB-": {
    clinicalBadge: "Universal Plasma Candidate / Rare RBC Recipient",
    canReceiveRbcFrom: ["AB-", "A-", "B-", "O-"],
    canDonateRbcTo: ["AB+", "AB-"],
    plasmaCanReceiveFrom: ["AB-"],
    plasmaCanDonateTo: ["AB-", "A-", "B-", "O-"],
    rarityInPopulation: "< 1% Population (Rarest Blood Phenotype)",
    emergencyUniversalStatus: "Highly preserved in blood banks; rare cell donor match"
  },
  "AB+": {
    clinicalBadge: "Universal Red Blood Cell (RBC) Recipient",
    canReceiveRbcFrom: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    canDonateRbcTo: ["AB+"],
    plasmaCanReceiveFrom: ["AB+"],
    plasmaCanDonateTo: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    rarityInPopulation: "~3% - 4% Population",
    emergencyUniversalStatus: "Universal recipient for red blood cells; Universal donor for plasma"
  }
};

export const SAMPLE_CASES = [
  {
    id: "CASE-01",
    label: "Sample Cassette 01 (A-Positive Clinical Case)",
    expectedGroup: "A+" as BloodGroup,
    profile: [1, 0, 1],
    wellScores: { a: 82.4, b: 24.1, d: 79.5 },
    patient: { id: "P-8821", name: "Ananya Sharma", age: 26, gender: "Female" as const, heightCm: 162, weightKg: 58 }
  },
  {
    id: "CASE-02",
    label: "Sample Cassette 02 (O-Negative Universal Emergency)",
    expectedGroup: "O-" as BloodGroup,
    profile: [0, 0, 0],
    wellScores: { a: 21.2, b: 19.8, d: 23.4 },
    patient: { id: "P-8822", name: "Vikramaditya Roy", age: 34, gender: "Male" as const, heightCm: 178, weightKg: 74 }
  },
  {
    id: "CASE-03",
    label: "Sample Cassette 03 (B-Positive High Clump Reaction)",
    expectedGroup: "B+" as BloodGroup,
    profile: [0, 1, 1],
    wellScores: { a: 22.8, b: 89.2, d: 84.7 },
    patient: { id: "P-8823", name: "David Chen", age: 41, gender: "Male" as const, heightCm: 172, weightKg: 69 }
  },
  {
    id: "CASE-04",
    label: "Sample Cassette 04 (AB-Negative Rare Phenotype)",
    expectedGroup: "AB-" as BloodGroup,
    profile: [1, 1, 0],
    wellScores: { a: 86.1, b: 81.3, d: 25.0 },
    patient: { id: "P-8824", name: "Priya Nair", age: 29, gender: "Female" as const, heightCm: 158, weightKg: 52 }
  }
];

export function calculateNadlerTBV(heightCm: number, weightKg: number, gender: "Male" | "Female"): {
  tbvLiters: number;
  maxSafeDonationMl: number;
  eligibilityStatus: string;
  isEligible: boolean;
  pctDrawn: number;
} {
  const hM = heightCm / 100.0;
  let tbvLiters = 0;
  if (gender === "Male") {
    tbvLiters = 0.3669 * Math.pow(hM, 3) + 0.03219 * weightKg + 0.6041;
  } else {
    tbvLiters = 0.3561 * Math.pow(hM, 3) + 0.03308 * weightKg + 0.1833;
  }

  let maxSafeDonationMl = 0;
  let isEligible = false;
  let eligibilityStatus = "";

  if (weightKg < 50) {
    eligibilityStatus = "Ineligible (Weight < 50 kg safety threshold)";
    maxSafeDonationMl = 0;
    isEligible = false;
  } else if (weightKg >= 60 && tbvLiters >= 4.2) {
    maxSafeDonationMl = 450;
    isEligible = true;
    eligibilityStatus = "Eligible for Full 450 mL Standard Blood Donation Unit";
  } else {
    maxSafeDonationMl = 350;
    isEligible = true;
    eligibilityStatus = "Eligible for 350 mL Pediatric / Moderate Voluntary Donation Unit";
  }

  const pctDrawn = tbvLiters > 0 ? (maxSafeDonationMl / (tbvLiters * 1000)) * 100 : 0;
  return {
    tbvLiters: Number(tbvLiters.toFixed(2)),
    maxSafeDonationMl,
    eligibilityStatus,
    isEligible,
    pctDrawn: Number(pctDrawn.toFixed(1))
  };
}
