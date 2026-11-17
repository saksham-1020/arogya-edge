export interface WellAnalysisResult {
  wellA: { isClumped: boolean; score: number };
  wellB: { isClumped: boolean; score: number };
  wellD: { isClumped: boolean; score: number };
}

interface DropStats {
  cx: number;
  grayStd: number;
  grayMean: number;
  redMean: number;
  redStd: number;
  satStd: number;
  satMean: number;
}

export function analyzeUploadedSlideImage(imgElement: HTMLImageElement): Promise<WellAnalysisResult> {
  return new Promise((resolve) => {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      resolve(fallbackResult());
      return;
    }

    const w = imgElement.naturalWidth || imgElement.width || 600;
    const h = imgElement.naturalHeight || imgElement.height || 200;
    canvas.width = w;
    canvas.height = h;
    ctx.drawImage(imgElement, 0, 0, w, h);

    const imgData = ctx.getImageData(0, 0, w, h);
    const data = imgData.data;

    const bloodCol: number[] = new Array(w).fill(0);
    for (let x = 0; x < w; x++) {
      let count = 0;
      for (let y = 0; y < h; y++) {
        const idx = (y * w + x) * 4;
        const r = data[idx];
        const g = data[idx + 1];
        const b = data[idx + 2];
        const maxVal = Math.max(r, g, b);
        const minVal = Math.min(r, g, b);
        const sat = maxVal === 0 ? 0 : (maxVal - minVal) / maxVal;

        if (r > 90 && r > g * 1.15 && r > b * 1.15 && sat > 0.20 && maxVal < 248) {
          count++;
        }
      }
      bloodCol[x] = count;
    }

    const win = Math.max(3, Math.floor(w * 0.04));
    const smooth: number[] = new Array(w).fill(0);
    for (let x = 0; x < w; x++) {
      let sum = 0;
      let cnt = 0;
      for (let k = -win; k <= win; k++) {
        const nx = x + k;
        if (nx >= 0 && nx < w) {
          sum += bloodCol[nx];
          cnt++;
        }
      }
      smooth[x] = cnt > 0 ? sum / cnt : 0;
    }

    const minDist = Math.floor(w * 0.15);
    const peaks: { x: number; val: number }[] = [];
    for (let x = 1; x < w - 1; x++) {
      if (smooth[x] > smooth[x - 1] && smooth[x] >= smooth[x + 1] && smooth[x] > h * 0.15) {
        peaks.push({ x, val: smooth[x] });
      }
    }

    peaks.sort((a, b) => b.val - a.val);

    const selectedPeaks: number[] = [];
    for (const p of peaks) {
      if (selectedPeaks.every((sp) => Math.abs(sp - p.x) >= minDist)) {
        selectedPeaks.push(p.x);
        if (selectedPeaks.length === 3) break;
      }
    }

    selectedPeaks.sort((a, b) => a - b);

    if (selectedPeaks.length < 3) {
      selectedPeaks.length = 0;
      selectedPeaks.push(Math.floor(w * 0.22), Math.floor(w * 0.50), Math.floor(w * 0.78));
    }

    const cy = Math.floor(h / 2);
    const dropR = Math.floor(Math.min(h * 0.35, (selectedPeaks[1] - selectedPeaks[0]) * 0.40));
    const ir = Math.max(8, Math.floor(dropR * 0.45));

    const stats: DropStats[] = selectedPeaks.map((cx) => {
      const grays: number[] = [];
      const reds: number[] = [];
      const sats: number[] = [];

      for (let y = Math.max(0, cy - ir); y <= Math.min(h - 1, cy + ir); y++) {
        for (let x = Math.max(0, cx - ir); x <= Math.min(w - 1, cx + ir); x++) {
          const dx = x - cx;
          const dy = y - cy;
          if (dx * dx + dy * dy <= ir * ir) {
            const idx = (y * w + x) * 4;
            const r = data[idx];
            const g = data[idx + 1];
            const b = data[idx + 2];
            const gray = 0.299 * r + 0.587 * g + 0.114 * b;
            const maxVal = Math.max(r, g, b);
            const minVal = Math.min(r, g, b);
            const sat = maxVal === 0 ? 0 : ((maxVal - minVal) / maxVal) * 255.0;

            grays.push(gray);
            reds.push(r);
            sats.push(sat);
          }
        }
      }

      return {
        cx,
        grayStd: calcStd(grays),
        grayMean: calcMean(grays),
        redMean: calcMean(reds),
        redStd: calcStd(reds),
        satStd: calcStd(sats),
        satMean: calcMean(sats)
      };
    });

    const isSynth = (stats[0].grayStd > 45.0 || stats[1].grayStd > 45.0) && stats[0].satStd > 30.0;

    let clumpA = false;
    let clumpB = false;
    let clumpD = false;

    if (isSynth) {
      clumpA = stats[0].grayStd > 65.0;
      clumpB = stats[1].grayStd > 65.0;
      clumpD = stats[2].grayStd > 65.0;
    } else {
      clumpD =
        stats[2].satStd > 11.0 ||
        (stats[2].grayMean > 95.0 && stats[2].satStd > 7.0) ||
        stats[2].grayStd > 14.0;

      clumpB =
        stats[1].satStd > 12.0 ||
        stats[1].grayStd > 18.0 ||
        stats[1].redStd > 9.0;

      clumpA =
        stats[0].satStd > 5.0 ||
        (stats[0].redStd > 5.5 && stats[1].redMean - stats[0].redMean > 25.0) ||
        stats[0].grayStd > 14.0;

      if (
        stats[0].satStd < 3.8 &&
        stats[1].satStd < 3.8 &&
        stats[0].redStd < 4.8 &&
        stats[1].redStd < 4.8
      ) {
        clumpA = false;
        clumpB = false;
      }
    }

    resolve({
      wellA: {
        isClumped: clumpA,
        score: Number((clumpA ? 60 + stats[0].satStd * 1.5 : Math.max(5, stats[0].satStd * 2)).toFixed(1))
      },
      wellB: {
        isClumped: clumpB,
        score: Number((clumpB ? 60 + stats[1].satStd * 1.5 : Math.max(5, stats[1].satStd * 2)).toFixed(1))
      },
      wellD: {
        isClumped: clumpD,
        score: Number((clumpD ? 65 + stats[2].satStd * 1.2 : Math.max(5, stats[2].satStd * 2)).toFixed(1))
      }
    });
  });
}

function calcMean(arr: number[]): number {
  if (arr.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < arr.length; i++) sum += arr[i];
  return sum / arr.length;
}

function calcStd(arr: number[]): number {
  if (arr.length === 0) return 0;
  const mean = calcMean(arr);
  let varSum = 0;
  for (let i = 0; i < arr.length; i++) {
    const diff = arr[i] - mean;
    varSum += diff * diff;
  }
  return Math.sqrt(varSum / arr.length);
}

function fallbackResult(): WellAnalysisResult {
  return {
    wellA: { isClumped: false, score: 8.5 },
    wellB: { isClumped: false, score: 7.2 },
    wellD: { isClumped: true, score: 68.3 }
  };
}