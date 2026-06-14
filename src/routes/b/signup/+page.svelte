<script lang="ts">
  import rawSummaries from '$lib/data/district_summaries.json';

  type DistrictEntry = { slug: string };
  const summaries = rawSummaries as Record<string, DistrictEntry>;

  const allDistricts = Object.entries(summaries)
    .map(([name, s]) => ({ name, slug: s.slug }))
    .sort((a, b) => a.name.localeCompare(b.name));

  let displayName = $state('');
  let agency      = $state('');
  let slug        = $state('');
  let bio         = $state('');
  let email       = $state('');
  let selectedDistricts = $state<string[]>([]);
  let photoFile   = $state<File | null>(null);
  let photoPreview = $state<string | null>(null);
  let slugManuallyEdited = $state(false);

  let status   = $state<'idle' | 'loading' | 'success' | 'error'>('idle');
  let errorMsg = $state('');

  function toSlug(name: string) {
    return name.toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-');
  }

  $effect(() => {
    if (displayName && !slugManuallyEdited) slug = toSlug(displayName);
  });

  function onSlugInput(e: Event) {
    slugManuallyEdited = true;
    slug = (e.target as HTMLInputElement).value.toLowerCase().replace(/[^a-z0-9-]/g, '');
  }

  function onPhotoChange(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    photoFile = file;
    photoPreview = URL.createObjectURL(file);
  }

  async function submit(e: Event) {
    e.preventDefault();
    if (status === 'loading') return;
    status = 'loading';
    errorMsg = '';

    try {
      const { supabase } = await import('$lib/supabase');
      if (!supabase) throw new Error('Service not available — try again shortly.');

      let photo_url: string | null = null;

      if (photoFile) {
        const ext  = photoFile.name.split('.').pop() ?? 'jpg';
        const path = `${slug}/${Date.now()}.${ext}`;
        const { error: uploadErr } = await supabase.storage
          .from('broker-photos')
          .upload(path, photoFile, { upsert: true });
        if (uploadErr) throw uploadErr;
        photo_url = supabase.storage.from('broker-photos').getPublicUrl(path).data.publicUrl;
      }

      const { error: insertErr } = await supabase.from('brokers').insert({
        slug,
        display_name: displayName.trim(),
        agency:       agency.trim()  || null,
        bio:          bio.trim()     || null,
        email:        email.trim().toLowerCase(),
        photo_url,
        districts:    selectedDistricts,
      });

      if (insertErr) {
        if (insertErr.code === '23505') {
          errorMsg = `adinteract.co/b/${slug} is already taken — try a different name.`;
          status = 'error';
          return;
        }
        throw insertErr;
      }

      status = 'success';
    } catch (err: unknown) {
      errorMsg = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      status = 'error';
    }
  }
</script>

<svelte:head>
  <title>Claim your ADInteract broker page</title>
  <meta name="description" content="Get a free co-branded Abu Dhabi property data page. Your name, your districts, 96,847 ADREC transactions. One link to share with any client." />
</svelte:head>

<div class="min-h-screen bg-[#0a2318] flex flex-col">

  <div class="border-b border-white/10 px-6 py-4 flex items-center justify-between">
    <a href="/" class="flex items-baseline gap-1">
      <span class="text-[#dfb83c] font-black text-lg tracking-wide">AD</span>
      <span class="text-[#C8A951] font-normal italic text-xs tracking-widest">INTERACT</span>
    </a>
    <span class="text-white/30 text-xs">Broker signup</span>
  </div>

  <div class="flex-1 flex items-start justify-center px-4 py-12">

    {#if status === 'success'}
      <div class="w-full max-w-lg text-center py-16">
        <div class="w-16 h-16 rounded-full bg-[#dfb83c]/20 flex items-center justify-center mx-auto mb-6">
          <svg class="w-8 h-8 text-[#dfb83c]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <h1 class="text-3xl font-black text-white mb-3">Your page is live.</h1>
        <p class="text-white/50 mb-8">Share this link with any client — it pulls live ADREC data every time they open it.</p>
        <a
          href="/b/{slug}"
          class="inline-block bg-[#dfb83c] text-[#0a2318] font-black px-8 py-4 rounded-xl text-base hover:bg-[#c9a830] transition-colors"
        >
          adinteract.co/b/{slug} →
        </a>
      </div>

    {:else}
      <div class="w-full max-w-lg">
        <h1 class="text-3xl font-black text-white mb-2">Claim your data page.</h1>
        <p class="text-white/40 text-sm mb-10">Your name. Your districts. 96,847 ADREC transactions. One link to send any client. Free.</p>

        <form onsubmit={submit} class="space-y-6">

          <!-- Photo -->
          <div>
            <p class="text-[10px] font-bold text-[#dfb83c] tracking-widest uppercase mb-3">Your photo</p>
            <div class="flex items-center gap-4">
              {#if photoPreview}
                <img src={photoPreview} alt="Preview" class="w-16 h-16 rounded-full object-cover border-2 border-[#dfb83c] flex-shrink-0"/>
              {:else}
                <div class="w-16 h-16 rounded-full bg-white/10 border-2 border-dashed border-white/20 flex items-center justify-center flex-shrink-0">
                  <svg class="w-6 h-6 text-white/25" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
                  </svg>
                </div>
              {/if}
              <label class="cursor-pointer bg-white/10 hover:bg-white/20 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
                {photoPreview ? 'Change photo' : 'Upload photo'}
                <input type="file" accept="image/*" class="hidden" onchange={onPhotoChange}/>
              </label>
            </div>
          </div>

          <!-- Name -->
          <div>
            <label for="display-name" class="block text-[10px] font-bold text-[#dfb83c] tracking-widest uppercase mb-2">Full name *</label>
            <input
              id="display-name"
              type="text"
              bind:value={displayName}
              placeholder="Sarah Jones"
              required
              class="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder:text-white/25 text-sm focus:outline-none focus:border-[#dfb83c] focus:ring-1 focus:ring-[#dfb83c]"
            />
          </div>

          <!-- Agency -->
          <div>
            <label for="agency" class="block text-[10px] font-bold text-[#dfb83c] tracking-widest uppercase mb-2">Agency</label>
            <input
              id="agency"
              type="text"
              bind:value={agency}
              placeholder="Betterhomes, Allsopp & Allsopp…"
              class="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder:text-white/25 text-sm focus:outline-none focus:border-[#dfb83c] focus:ring-1 focus:ring-[#dfb83c]"
            />
          </div>

          <!-- Slug -->
          <div>
            <label for="slug" class="block text-[10px] font-bold text-[#dfb83c] tracking-widest uppercase mb-2">Your page URL *</label>
            <div class="flex items-center bg-white/10 border border-white/20 rounded-lg overflow-hidden focus-within:border-[#dfb83c] focus-within:ring-1 focus-within:ring-[#dfb83c]">
              <span class="text-white/35 text-sm pl-4 pr-1 flex-shrink-0 whitespace-nowrap">adinteract.co/b/</span>
              <input
                id="slug"
                type="text"
                value={slug}
                oninput={onSlugInput}
                placeholder="sarah-jones"
                required
                class="flex-1 bg-transparent py-3 pr-4 text-white text-sm focus:outline-none min-w-0"
              />
            </div>
          </div>

          <!-- Bio -->
          <div>
            <label for="bio" class="block text-[10px] font-bold text-[#dfb83c] tracking-widest uppercase mb-2">One-line bio</label>
            <input
              id="bio"
              type="text"
              bind:value={bio}
              placeholder="Abu Dhabi specialist · 10 years · Reem & Saadiyat"
              maxlength={120}
              class="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder:text-white/25 text-sm focus:outline-none focus:border-[#dfb83c] focus:ring-1 focus:ring-[#dfb83c]"
            />
          </div>

          <!-- Email -->
          <div>
            <label for="email" class="block text-[10px] font-bold text-[#dfb83c] tracking-widest uppercase mb-2">Email *</label>
            <input
              id="email"
              type="email"
              bind:value={email}
              placeholder="you@agency.com"
              required
              class="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder:text-white/25 text-sm focus:outline-none focus:border-[#dfb83c] focus:ring-1 focus:ring-[#dfb83c]"
            />
          </div>

          <!-- Districts -->
          <div>
            <p class="text-[10px] font-bold text-[#dfb83c] tracking-widest uppercase mb-1">Districts you cover</p>
            <p class="text-white/30 text-xs mb-3">Select all that apply — ADREC data loads for each one.</p>
            <div class="max-h-56 overflow-y-auto bg-white/5 border border-white/10 rounded-lg p-3 grid grid-cols-2 gap-y-2 gap-x-3">
              {#each allDistricts as d}
                <label class="flex items-start gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    bind:group={selectedDistricts}
                    value={d.slug}
                    class="mt-0.5 w-3.5 h-3.5 flex-shrink-0 rounded border-white/30 bg-white/10 accent-[#dfb83c] cursor-pointer"
                  />
                  <span class="text-xs text-white/60 group-hover:text-white/90 transition-colors leading-tight">{d.name}</span>
                </label>
              {/each}
            </div>
            {#if selectedDistricts.length > 0}
              <p class="text-[#dfb83c] text-xs mt-2">{selectedDistricts.length} district{selectedDistricts.length === 1 ? '' : 's'} selected</p>
            {/if}
          </div>

          {#if errorMsg}
            <p class="text-red-400 text-sm">{errorMsg}</p>
          {/if}

          <button
            type="submit"
            disabled={status === 'loading'}
            class="w-full bg-[#dfb83c] hover:bg-[#c9a830] disabled:opacity-60 text-[#0a2318] font-black py-4 rounded-xl text-base transition-colors"
          >
            {status === 'loading' ? 'Building your page…' : 'Build my page →'}
          </button>

          <p class="text-white/20 text-xs text-center">Free forever. No account needed. Data updates daily from ADREC.</p>

        </form>
      </div>
    {/if}

  </div>
</div>
