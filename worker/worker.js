export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Content-Type': 'application/json'
    };

    if (request.method === 'OPTIONS') return new Response(null, { headers: cors });

    try {
      // ── EXISTING: milestone + scores data ──────────────────────
      if (request.method === 'GET' && url.pathname === '/data') {
        const raw = await env.HAILO_KV.get('hailo_data');
        const data = raw ? JSON.parse(raw) : { milestones: [], scores: {} };
        return new Response(JSON.stringify(data), { headers: cors });
      }
      if (request.method === 'PUT' && url.pathname === '/data') {
        const body = await request.json();
        await env.HAILO_KV.put('hailo_data', JSON.stringify(body));
        return new Response(JSON.stringify({ ok: true }), { headers: cors });
      }

      // ── NEW: quiz questions ─────────────────────────────────────
      if (request.method === 'GET' && url.pathname === '/quiz-questions') {
        const raw = await env.HAILO_KV.get('quiz_questions');
        const data = raw ? JSON.parse(raw) : [];
        return new Response(JSON.stringify(data), { headers: cors });
      }
      if (request.method === 'PUT' && url.pathname === '/quiz-questions') {
        const body = await request.json();
        await env.HAILO_KV.put('quiz_questions', JSON.stringify(body));
        return new Response(JSON.stringify({ ok: true }), { headers: cors });
      }

      return new Response(JSON.stringify({ error: 'Not found' }), { status: 404, headers: cors });
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), { status: 500, headers: cors });
    }
  }
};
