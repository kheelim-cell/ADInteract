<script lang="ts">
  export type ExtractionData = {
    projectName:       string | null;
    developer:         string | null;
    district:          string | null;
    layout:            string | null;
    cost:              number | null;
    size:              number | null;
    yearsTillHandover: number | null;
    serviceChargePsf:  number | null;
  };

  import { m } from '$lib/paraglide/messages.js';

  type Props = {
    onExtracted: (data: ExtractionData) => void;
  };

  let { onExtracted }: Props = $props();

  type Status = 'idle' | 'processing' | 'done' | 'error';

  let status      = $state<Status>('idle');
  let errorMsg    = $state('');
  let previews    = $state<string[]>([]);
  let fileNames   = $state<string[]>([]);
  let isDragging  = $state(false);
  let currentFile = $state(0);   // 1-based, which file is being processed now
  let totalFiles  = $state(0);

  const MAX_IMG_MB  = 20;
  const MAX_PDF_MB  = 20;
  const MAX_FILES   = 5;
  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'application/pdf'];

  async function toBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload  = () => resolve((reader.result as string).split(',')[1]);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  // Render a PDF to a JPEG image client-side using PDF.js so the payload
  // sent to the server is always small (a JPEG, not the raw PDF bytes).
  async function pdfToJpegBase64(file: File): Promise<string> {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const pdfjs: any = await import(/* @vite-ignore */ 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.3.136/build/pdf.min.mjs');
    pdfjs.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.3.136/build/pdf.worker.min.mjs';
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjs.getDocument({ data: new Uint8Array(arrayBuffer) }).promise;
    const pageCount = Math.min(pdf.numPages, 32);
    const canvases: HTMLCanvasElement[] = [];
    for (let p = 1; p <= pageCount; p++) {
      const page = await pdf.getPage(p);
      const viewport = page.getViewport({ scale: 1.0 });
      const canvas = document.createElement('canvas');
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      await page.render({ canvasContext: canvas.getContext('2d')!, viewport }).promise;
      canvases.push(canvas);
    }
    // Stitch pages vertically into one image
    const totalH = canvases.reduce((s, c) => s + c.height, 0);
    const merged = document.createElement('canvas');
    merged.width = canvases[0].width;
    merged.height = totalH;
    const ctx = merged.getContext('2d')!;
    let y = 0;
    for (const c of canvases) { ctx.drawImage(c, 0, y); y += c.height; }
    return merged.toDataURL('image/jpeg', 0.85).split(',')[1];
  }

  // Compress images client-side to stay well under Vercel's 4.5 MB limit
  async function toBase64Compressed(file: File): Promise<string> {
    if (file.type === 'application/pdf') return toBase64(file);
    const TARGET = 1.5 * 1024 * 1024;
    if (file.size <= TARGET) return toBase64(file);
    return new Promise((resolve, reject) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        URL.revokeObjectURL(url);
        const canvas = document.createElement('canvas');
        let { width, height } = img;
        const maxDim = 2048;
        if (width > maxDim || height > maxDim) {
          const ratio = Math.min(maxDim / width, maxDim / height);
          width = Math.round(width * ratio);
          height = Math.round(height * ratio);
        }
        canvas.width = width; canvas.height = height;
        canvas.getContext('2d')!.drawImage(img, 0, 0, width, height);
        resolve(canvas.toDataURL('image/jpeg', 0.85).split(',')[1]);
      };
      img.onerror = () => { URL.revokeObjectURL(url); toBase64(file).then(resolve).catch(reject); };
      img.src = url;
    });
  }

  async function extractOne(file: File): Promise<ExtractionData> {
    let base64Data: string;
    let mediaType = file.type;
    if (file.type === 'application/pdf') {
      base64Data = await pdfToJpegBase64(file);
      mediaType = 'image/jpeg';
    } else {
      base64Data = await toBase64Compressed(file);
    }
    const res = await fetch('/api/extract-property', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ fileData: base64Data, mediaType }),
    });
    if (!res.ok) {
      const txt = await res.text().catch(() => res.statusText);
      throw new Error(txt.slice(0, 250));
    }
    const json = await res.json();
    return json.data as ExtractionData;
  }

  // First non-null value wins across all results
  function mergeResults(results: ExtractionData[]): ExtractionData {
    const merged: ExtractionData = {
      projectName: null, developer: null, district: null, layout: null,
      cost: null, size: null, yearsTillHandover: null, serviceChargePsf: null,
    };
    for (const r of results) {
      for (const key of Object.keys(merged) as (keyof ExtractionData)[]) {
        if (merged[key] == null && r[key] != null) {
          (merged as Record<string, unknown>)[key] = r[key];
        }
      }
    }
    return merged;
  }

  async function handleFiles(files: File[]) {
    status      = 'idle';
    errorMsg    = '';
    previews    = [];
    fileNames   = [];
    currentFile = 0;

    for (const file of files) {
      const isPdf = file.type === 'application/pdf';
      const maxMb = isPdf ? MAX_PDF_MB : MAX_IMG_MB;
      if (file.size > maxMb * 1024 * 1024) {
        status   = 'error';
        errorMsg = isPdf
          ? m.upload_error_pdf_too_large({ name: file.name, size: (file.size / 1024 / 1024).toFixed(1), max: String(MAX_PDF_MB) })
          : m.upload_error_img_too_large({ name: file.name, size: (file.size / 1024 / 1024).toFixed(1), max: String(MAX_IMG_MB) });
        return;
      }
      if (!ALLOWED_TYPES.includes(file.type)) {
        status   = 'error';
        errorMsg = m.upload_error_unsupported_type({ name: file.name });
        return;
      }
    }

    fileNames  = files.map(f => f.name);
    totalFiles = files.length;
    previews   = files.map(f => f.type.startsWith('image/') ? URL.createObjectURL(f) : '');
    status     = 'processing';

    const results: ExtractionData[] = [];
    for (let i = 0; i < files.length; i++) {
      currentFile = i + 1;
      try {
        const data = await extractOne(files[i]);
        results.push(data);
      } catch (e: unknown) {
        status   = 'error';
        errorMsg = m.upload_error_file_failed({
          n: String(i + 1),
          total: String(files.length),
          message: e instanceof Error ? e.message : m.upload_error_extraction_failed_default()
        });
        return;
      }
    }

    status = 'done';
    onExtracted(mergeResults(results));
  }

  function onInputChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const files = Array.from(input.files ?? []).slice(0, MAX_FILES);
    if (files.length) handleFiles(files);
    input.value = '';
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
    const files = Array.from(e.dataTransfer?.files ?? []).slice(0, MAX_FILES);
    if (files.length) handleFiles(files);
  }

  function reset() {
    status      = 'idle';
    previews    = [];
    fileNames   = [];
    errorMsg    = '';
    currentFile = 0;
    totalFiles  = 0;
  }
</script>

<div class="rounded-xl border border-white/15 bg-white/3 overflow-hidden">

  {#if status === 'idle' || status === 'error'}
    <!-- ── Drop zone ── -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <label
      class="flex flex-col items-center gap-2.5 px-5 py-5 cursor-pointer transition-colors
        {isDragging ? 'bg-amber-500/10 border-amber-500/40' : 'hover:bg-white/4'}"
      ondragover={(e) => { e.preventDefault(); isDragging = true; }}
      ondragleave={() => { isDragging = false; }}
      ondrop={onDrop}
    >
      <input type="file" accept="image/*,.pdf" multiple class="sr-only" onchange={onInputChange} />

      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-amber-500/15 flex items-center justify-center flex-shrink-0">
          <svg class="w-4.5 h-4.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
          </svg>
        </div>
        <div>
          <p class="text-xs font-semibold text-white/80">
            {isDragging ? m.upload_drop_to_scan() : m.upload_offplan_title()}
          </p>
          <p class="text-[11px] text-white/30 mt-0.5">{m.upload_file_types_hint({ max: String(MAX_FILES), mb: String(MAX_IMG_MB) })}</p>
        </div>
      </div>

      {#if status === 'error'}
        <p class="text-[11px] text-red-400 font-medium">{errorMsg}</p>
      {/if}
    </label>

  {:else if status === 'processing'}
    <!-- ── Loading ── -->
    <div class="flex items-center gap-3 px-5 py-4">
      <svg class="w-4 h-4 text-amber-400 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
      <div class="flex-1 min-w-0">
        <p class="text-xs font-medium text-white/70">
          {m.upload_extracting({ current: String(currentFile), total: String(totalFiles) })}
        </p>
        <p class="text-[11px] text-white/30 truncate mt-0.5">{fileNames[currentFile - 1] ?? ''}</p>
      </div>
      <!-- Thumbnails: show already-queued images -->
      {#if previews.some(p => p)}
        <div class="flex gap-1 flex-shrink-0">
          {#each previews as src, i}
            {#if src}
              <img
                {src} alt="preview {i + 1}"
                class="w-8 h-8 rounded-md object-cover border flex-shrink-0
                  {i + 1 === currentFile ? 'border-amber-400' : 'border-white/10 opacity-40'}"
              />
            {/if}
          {/each}
        </div>
      {/if}
    </div>

  {:else if status === 'done'}
    <!-- ── Success ── -->
    <div class="flex items-center gap-3 px-4 py-3">
      <!-- Thumbnails or icon -->
      {#if previews.some(p => p)}
        <div class="flex gap-1 flex-shrink-0">
          {#each previews as src, i}
            {#if src}
              <img src={src} alt="preview {i + 1}" class="w-9 h-9 rounded-lg object-cover border border-white/10 flex-shrink-0" />
            {/if}
          {/each}
        </div>
      {:else}
        <div class="w-9 h-9 rounded-xl bg-emerald-500/15 flex items-center justify-center flex-shrink-0">
          <svg class="w-4.5 h-4.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        </div>
      {/if}
      <div class="flex-1 min-w-0">
        <p class="text-xs font-semibold text-emerald-400">
          {totalFiles === 1 ? m.upload_extraction_complete() : m.upload_files_scanned({ n: String(totalFiles) })} {m.upload_prefilled_suffix()}
        </p>
        <p class="text-[11px] text-white/30 truncate mt-0.5">
          {fileNames.join(' · ')}
        </p>
      </div>
      <button
        type="button"
        onclick={reset}
        class="flex-shrink-0 text-[11px] text-white/25 hover:text-white/55 transition-colors underline underline-offset-2"
      >
        {m.upload_clear()}
      </button>
    </div>
  {/if}

</div>
