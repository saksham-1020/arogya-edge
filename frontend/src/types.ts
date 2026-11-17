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
  biologicalExplanation: {
    summary: string;
    whyThisGroup: string;
    antigensPresent: string;
    antibodiesInPlasma: string;
    reagentClumpingBreakdown: {
      wellA: string;
      wellB: string;
      wellD: string;
    };
    identificationRule: string;
  };
}

export const BLOOD_COMPATIBILITY: Record<BloodGroup, CompatibilityData> = {
  "O-": {
    clinicalBadge: "Universal Red Blood Cell (RBC) Donor",
    canReceiveRbcFrom: ["O-"],
    canDonateRbcTo: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    plasmaCanReceiveFrom: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    plasmaCanDonateTo: ["O-"],
    rarityInPopulation: "~7% Global (Critical Emergency Reserve)",
    emergencyUniversalStatus: "🚨 Standard Emergency Trauma Choice (Safe for all recipients prior to cross-matching)",
    biologicalExplanation: {
      summary: "Teeno drops smooth (unclumped) rahe, koi clumping nahi hui.",
      whyThisGroup: "Khoon ke RBCs par na toh A antigen hai, na B antigen, aur na hi Rh(D) protein hai. Isliye kisi bhi reagent ne reaction nahi diya.",
      antigensPresent: "None (Zero ABO & Rh Antigens on RBC surface)",
      antibodiesInPlasma: "Anti-A, Anti-B, and potential Anti-D antibodies",
      reagentClumpingBreakdown: {
        wellA: "Smooth / No Reaction (Anti-A antibodies ko bind karne ke liye A antigen nahi mila)",
        wellB: "Smooth / No Reaction (Anti-B antibodies ko bind karne ke liye B antigen nahi mila)",
        wellD: "Smooth / No Reaction (Rh factor absent hai, isliye blood Rh-Negative hai)"
      },
      identificationRule: "Well-A (-), Well-B (-), Well-D (-) = Complete Absence of Antigens &rarr; Group O-Negative"
    }
  },
  "O+": {
    clinicalBadge: "Universal Positive RBC Donor",
    canReceiveRbcFrom: ["O+", "O-"],
    canDonateRbcTo: ["O+", "A+", "B+", "AB+"],
    plasmaCanReceiveFrom: ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"],
    plasmaCanDonateTo: ["O+", "A+", "B+", "AB+"],
    rarityInPopulation: "~38% (Most Common Worldwide)",
    emergencyUniversalStatus: "Most widely transfused red cell unit in clinical hospital networks",
    biologicalExplanation: {
      summary: "Sirf Well-D (Rh) clump hua, Well-A aur Well-B smooth rahe.",
      whyThisGroup: "RBCs par A aur B antigens nahi hain (isliye group 'O'), par Rh-D protein maujood hai (isliye Positive '+').",
      antigensPresent: "Rh(D) Antigen only (No A or B antigens)",
      antibodiesInPlasma: "Anti-A and Anti-B antibodies",
      reagentClumpingBreakdown: {
        wellA: "Smooth / No Clumping (A antigen absent hai)",
        wellB: "Smooth / No Clumping (B antigen absent hai)",
        wellD: "Clumped / Granular Clumping (Anti-D ne RBC par maujood Rh protein ko bind kiya)"
      },
      identificationRule: "Well-A (-), Well-B (-), Well-D (+) = Group O-Positive"
    }
  },
  "A-": {
    clinicalBadge: "Rh-Negative A Donor",
    canReceiveRbcFrom: ["A-", "O-"],
    canDonateRbcTo: ["A+", "A-", "AB+", "AB-"],
    plasmaCanReceiveFrom: ["A-", "A+", "AB-", "AB+"],
    plasmaCanDonateTo: ["A-", "O-"],
    rarityInPopulation: "~6% Population",
    emergencyUniversalStatus: "High demand for negative-group trauma cases",
    biologicalExplanation: {
      summary: "Sirf Well-A clump hua; Well-B aur Well-D smooth rahe.",
      whyThisGroup: "RBCs par 'A' antigen maujood hai, par B antigen aur Rh factor dono absent hain.",
      antigensPresent: "Antigen A only (Rh-D Absent)",
      antibodiesInPlasma: "Anti-B antibodies (Plasma me)",
      reagentClumpingBreakdown: {
        wellA: "Clumped / Granular Clumping (Anti-A reagent ne A antigen ke sath agglutinate kiya)",
        wellB: "Smooth / No Reaction (B antigen absent hai)",
        wellD: "Smooth / No Reaction (Rh factor absent hone ki wajah se blood Negative hai)"
      },
      identificationRule: "Well-A (+), Well-B (-), Well-D (-) = Group A-Negative"
    }
  },
  "A+": {
    clinicalBadge: "Standard A-Positive Profile",
    canReceiveRbcFrom: ["A+", "A-", "O+", "O-"],
    canDonateRbcTo: ["A+", "AB+"],
    plasmaCanReceiveFrom: ["A+", "AB+"],
    plasmaCanDonateTo: ["A+", "A-", "O+", "O-"],
    rarityInPopulation: "~34% Population",
    emergencyUniversalStatus: "Second most common recipient cohort in emergency triage",
    biologicalExplanation: {
      summary: "Well-A aur Well-D dono clump hue; Well-B smooth raha.",
      whyThisGroup: "RBCs par Antigen A aur Rh-D protein dono present hain, jabki B antigen bilkul absent hai.",
      antigensPresent: "Antigen A and Rh(D) Antigen",
      antibodiesInPlasma: "Anti-B antibodies",
      reagentClumpingBreakdown: {
        wellA: "Clumped / Agglutinated (Anti-A antibodies ne A-antigens ko jodh kar khoon ke dane banaye)",
        wellB: "Smooth / No Reaction (Anti-B antibodies ko koi target antigen nahi mila)",
        wellD: "Clumped / Agglutinated (Anti-D antibodies ne Rh factor ko pehchaan kar clump kiya)"
      },
      identificationRule: "Well-A (+), Well-B (-), Well-D (+) = Group A-Positive"
    }
  },
  "B-": {
    clinicalBadge: "Rh-Negative B Donor",
    canReceiveRbcFrom: ["B-", "O-"],
    canDonateRbcTo: ["B+", "B-", "AB+", "AB-"],
    plasmaCanReceiveFrom: ["B-", "B+", "AB-", "AB+"],
    plasmaCanDonateTo: ["B-", "O-"],
    rarityInPopulation: "~2% Population (Very Rare in Western Countries, 15% in South Asia)",
    emergencyUniversalStatus: "Priority matching required to prevent RhD isoimmunization",
    biologicalExplanation: {
      summary: "Sirf Well-B clump hua; Well-A aur Well-D smooth rahe.",
      whyThisGroup: "RBCs par sirf 'B' antigen maujood hai; A antigen aur Rh protein dono absent hain.",
      antigensPresent: "Antigen B only (Rh-D Absent)",
      antibodiesInPlasma: "Anti-A antibodies",
      reagentClumpingBreakdown: {
        wellA: "Smooth / No Clumping (A antigen absent hai)",
        wellB: "Clumped / Strong Reaction (Anti-B ne B-antigens ko precipitate kiya)",
        wellD: "Smooth / No Clumping (Rh factor absent hone se blood Negative hai)"
      },
      identificationRule: "Well-A (-), Well-B (+), Well-D (-) = Group B-Negative"
    }
  },
  "B+": {
    clinicalBadge: "Standard B-Positive Profile",
    canReceiveRbcFrom: ["B+", "B-", "O+", "O-"],
    canDonateRbcTo: ["B+", "AB+"],
    plasmaCanReceiveFrom: ["B+", "AB+"],
    plasmaCanDonateTo: ["B+", "B-", "O+", "O-"],
    rarityInPopulation: "~9% Globally (High Prevalence in Asia)",
    emergencyUniversalStatus: "Key focus for voluntary whole blood and platelet apheresis",
    biologicalExplanation: {
      summary: "Well-B aur Well-D dono clump hue; Well-A smooth raha.",
      whyThisGroup: "RBCs par Antigen B aur Rh-D dono maujood hain, jabki Antigen A absent hai.",
      antigensPresent: "Antigen B and Rh(D) Antigen",
      antibodiesInPlasma: "Anti-A antibodies",
      reagentClumpingBreakdown: {
        wellA: "Smooth / No Reaction (Anti-A ko koi antigen nahi mila)",
        wellB: "Clumped / Agglutinated (Anti-B ne B antigen ke sath clumping banayi)",
        wellD: "Clumped / Agglutinated (Anti-D ne Rh factor ke sath clumping banayi)"
      },
      identificationRule: "Well-A (-), Well-B (+), Well-D (+) = Group B-Positive"
    }
  },
  "AB-": {
    clinicalBadge: "Universal Plasma Candidate / Rare RBC Recipient",
    canReceiveRbcFrom: ["AB-", "A-", "B-", "O-"],
    canDonateRbcTo: ["AB+", "AB-"],
    plasmaCanReceiveFrom: ["AB-"],
    plasmaCanDonateTo: ["AB-", "A-", "B-", "O-"],
    rarityInPopulation: "< 1% Population (Rarest Blood Phenotype)",
    emergencyUniversalStatus: "Highly preserved in blood banks; rare cell donor match",
    biologicalExplanation: {
      summary: "Well-A aur Well-B dono clump hue; Well-D smooth raha.",
      whyThisGroup: "RBCs par A aur B dono antigens co-dominant roop se present hain, par Rh factor absent hai.",
      antigensPresent: "Both Antigen A & Antigen B (Rh-D Absent)",
      antibodiesInPlasma: "Neither Anti-A nor Anti-B antibodies",
      reagentClumpingBreakdown: {
        wellA: "Clumped / Agglutinated (A antigen ne Anti-A ke sath react kiya)",
        wellB: "Clumped / Agglutinated (B antigen ne Anti-B ke sath react kiya)",
        wellD: "Smooth / No Reaction (Rh factor absent hai, isliye Rh-Negative)"
      },
      identificationRule: "Well-A (+), Well-B (+), Well-D (-) = Group AB-Negative"
    }
  },
  "AB+": {
    clinicalBadge: "Universal Red Blood Cell (RBC) Recipient",
    canReceiveRbcFrom: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    canDonateRbcTo: ["AB+"],
    plasmaCanReceiveFrom: ["AB+"],
    plasmaCanDonateTo: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    rarityInPopulation: "~3% - 4% Population",
    emergencyUniversalStatus: "Universal recipient for red blood cells; Universal donor for plasma",
    biologicalExplanation: {
      summary: "Teeno drops (Well-A, Well-B, Well-D) clump hue.",
      whyThisGroup: "RBCs par A, B aur Rh(D) teeno proteins fully express ho rahe hain. Isliye har reagent ne react karke blood ko clump kiya.",
      antigensPresent: "Antigen A, Antigen B, and Rh(D) Antigen (All Present)",
      antibodiesInPlasma: "None (Neither Anti-A nor Anti-B antibodies in plasma)",
      reagentClumpingBreakdown: {
        wellA: "Clumped / Agglutinated (A antigen confirmed)",
        wellB: "Clumped / Agglutinated (B antigen confirmed)",
        wellD: "Clumped / Agglutinated (Rh-D protein confirmed)"
      },
      identificationRule: "Well-A (+), Well-B (+), Well-D (+) = Group AB-Positive (Universal RBC Recipient)"
    }
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
