﻿﻿﻿// ── CACHE (dados locais vindos da API) ──
const cache = {
  layouts: [],
  campos: []
};

let PAGE_SIZE = parseInt(localStorage.getItem('pageSize'), 10) || 10;

function applyPageSize(value) {
  PAGE_SIZE = parseInt(value, 10) || 10;
  localStorage.setItem('pageSize', String(PAGE_SIZE));
  document.querySelectorAll('.page-size-select').forEach(sel => { sel.value = String(PAGE_SIZE); });
}
const state = {
  editingId: null,
  editingSection: null,
  deletingId: null,
  deletingSection: null,
  duplicatingId: null,
  duplicatingSection: null,
  pageNums: { layouts: 1, campos: 1 },
  filters: { layouts: '', campos: '' },
  loggedIn: false,
  user: null
};

const labels = {
  layouts: { singular: 'layout', plural: 'layouts' },
  campos: { singular: 'campo', plural: 'campos' }
};

// ── API ──
async function apiFetch(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' }, cache: 'no-store' };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw data;
  return data;
}

function syncRowSelection(state, slice) {
  if (slice.length === 0) {
    state.selectedId = null;
  } else if (!slice.some(r => r.id === state.selectedId)) {
    state.selectedId = slice[0].id;
  }
}

async function loadSection(section) {
  try {
    cache[section] = await apiFetch('GET', `/api/${section}`);
    renderTable(section);
  } catch {
    toast('Erro ao carregar dados');
  }
}

async function loadStats() {
  try {
    const stats = await apiFetch('GET', '/api/stats');
    const map = { conciliacao: 'stat-conc', layouts: 'stat-lay', campos: 'stat-campo' };
    Object.entries(map).forEach(([k, id]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = stats[k];
    });
  } catch { /* homepage stats são opcionais */ }
}

// ── TABLE RENDER ──
function filterTable(section) {
  state.filters[section] = document.getElementById('search-' + section).value.toLowerCase();
  state.pageNums[section] = 1;
  renderTable(section);
}

function getFiltered(section) {
  const q = state.filters[section];
  return cache[section].filter(r =>
    r.codigo.toLowerCase().includes(q) || r.descricao.toLowerCase().includes(q)
  );
}

function renderTable(section) {
  const filtered = getFiltered(section);
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg = Math.min(state.pageNums[section], totalPages);
  state.pageNums[section] = pg;

  const slice = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody = document.getElementById('tbody-' + section);
  const empty = document.getElementById('empty-' + section);
  const pag = document.getElementById('pag-' + section);

  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  pag.style.display = 'flex';

  tbody.innerHTML = slice.map(r => `
    <tr>
      <td><span class="td-code">${esc(r.codigo)}</span></td>
      <td>${esc(r.descricao)}</td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.criadoEm}</td>
      <td>
        <div class="td-actions">
          <button class="btn btn-secondary btn-sm" onclick="openForm('${section}',${r.id})">Editar</button>
          <button class="btn btn-secondary btn-sm" onclick="openDelete('${section}',${r.id})">Excluir</button>
        </div>
      </td>
    </tr>
  `).join('');

  const info = document.getElementById('pag-info-' + section);
  const start = (pg - 1) * PAGE_SIZE + 1;
  const end = Math.min(pg * PAGE_SIZE, total);
  info.textContent = `${start}–${end} de ${total}`;

  const btns = document.getElementById('pag-btns-' + section);
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changePage('${section}',-1)" ${pg===1?'disabled':''}>‹</button>`;
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoPage('${section}',${i})">${i}</button>`;
  }
  html += `<button class="pag-btn" onclick="changePage('${section}',1)" ${pg===totalPages?'disabled':''}>›</button>`;
  btns.innerHTML = html;
}

function changePage(section, dir) {
  const total = Math.max(1, Math.ceil(getFiltered(section).length / PAGE_SIZE));
  state.pageNums[section] = Math.max(1, Math.min(total, state.pageNums[section] + dir));
  renderTable(section);
}

function gotoPage(section, n) {
  state.pageNums[section] = n;
  renderTable(section);
}

// ── FORM ──
function openForm(section, id) {
  if (!state.loggedIn) { openModal('loginModal'); toast('Faça login para continuar'); return; }

  state.editingSection = section;
  state.editingId = id || null;

  document.getElementById('formTitle').textContent = id
    ? `Editar ${labels[section].singular}`
    : `Nova ${labels[section].singular}`;

  clearErrors();

  if (id) {
    const rec = cache[section].find(r => r.id === id);
    document.getElementById('formCodigo').value = rec.codigo;
    document.getElementById('formDescricao').value = rec.descricao;
  } else {
    document.getElementById('formCodigo').value = '';
    document.getElementById('formDescricao').value = '';
  }

  openModal('formModal');
}

async function saveRecord() {
  const codigo = document.getElementById('formCodigo').value.trim();
  const descricao = document.getElementById('formDescricao').value.trim();

  clearErrors();
  let valid = true;
  if (!codigo) { document.getElementById('errCodigo').style.display = 'block'; valid = false; }
  if (!descricao) { document.getElementById('errDescricao').style.display = 'block'; valid = false; }
  if (!valid) return;

  const section = state.editingSection;
  const id = state.editingId;

  try {
    if (id) {
      await apiFetch('PUT', `/api/${section}/${id}`, { codigo, descricao });
      toast(`${labels[section].singular} atualizado com sucesso`);
    } else {
      await apiFetch('POST', `/api/${section}`, { codigo, descricao });
      toast(`${labels[section].singular} criado com sucesso`);
    }
    closeModal('formModal');
    await loadSection(section);
  } catch (err) {
    if (err.error) {
      const el = document.getElementById('errCodigo');
      el.textContent = err.error;
      el.style.display = 'block';
    } else {
      toast('Erro ao salvar registro');
    }
  }
}

function clearErrors() {
  const el = document.getElementById('errCodigo');
  el.style.display = 'none';
  el.textContent = 'Código é obrigatório';
  document.getElementById('errDescricao').style.display = 'none';
}

// ── DELETE ──
function openDelete(section, id) {
  if (!state.loggedIn) { openModal('loginModal'); return; }
  state.deletingSection = section;
  state.deletingId = id;

  let displayName;
  if (section === 'users') {
    const u = usersCache.find(u => u.id === id);
    displayName = `"${u.name} (${u.username})"`;
  } else if (section === 'recon') {
    const r = reconCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'ds') {
    const r = dsCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'fields') {
    const r = fieldsCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'rules') {
    const r = rulesCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'rf') {
    const r = rfCache.find(r => r.id === id);
    displayName = `"${r.rule_name} / ${r.field1_name} / ${r.field2_name}"`;
  } else if (section === 'profiles') {
    const r = profilesCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'transactions') {
    const r = transactionsCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'profile_transaction') {
    const r = profileTransactionsCache.find(r => r.id === id);
    displayName = `"${r.profile_name} / ${r.transaction_name}"`;
  } else {
    const rec = cache[section].find(r => r.id === id);
    displayName = `"${rec.codigo} – ${rec.descricao}"`;
  }

  document.getElementById('deleteItemName').textContent = displayName;
  openModal('deleteModal');
}

async function confirmDelete() {
  const section = state.deletingSection;
  const id = state.deletingId;

  const apiPath = section === 'users'        ? `/api/user/${id}`
                : section === 'recon'        ? `/api/recon/${id}`
                : section === 'ds'           ? `/api/ds/${id}`
                : section === 'fields'       ? `/api/field/${id}`
                : section === 'rules'        ? `/api/rule/${id}`
                : section === 'rf'           ? `/api/rule_field/${id}`
                : section === 'profiles'     ? `/api/profile/${id}`
                : section === 'transactions' ? `/api/transaction/${id}`
                : section === 'profile_transaction' ? `/api/profile_transaction/${id}`
                : `/api/${section}/${id}`;

  try {
    await apiFetch('DELETE', apiPath);
    closeModal('deleteModal');
    if (section === 'users') {
      await loadUsers();
      toast('Usuário excluído');
    } else if (section === 'recon') {
      await loadRecon();
      toast('Conciliação excluída');
    } else if (section === 'ds') {
      await loadDatasource();
      toast('Fonte de dados excluída');
    } else if (section === 'fields') {
      await loadFields();
      toast('Campo excluído');
    } else if (section === 'rules') {
      await loadRules();
      toast('Regra excluída');
    } else if (section === 'rf') {
      await loadRuleField();
      toast('Regra x campo excluída');
    } else if (section === 'profiles') {
      await loadProfiles();
      toast('Perfil excluído');
    } else if (section === 'transactions') {
      await loadTransactions();
      toast('Transação excluída');
    } else if (section === 'profile_transaction') {
      await loadProfileTransactions();
      toast('Associação excluída');
    } else {
      await loadSection(section);
      toast(`${labels[section].singular} excluído`);
    }
  } catch (err) {
    toast(err.error || 'Erro ao excluir registro');
  }
}

// ── DUPLICATE ──
function openDuplicate(section, id) {
  if (!state.loggedIn) { openModal('loginModal'); return; }
  state.duplicatingSection = section;
  state.duplicatingId = id;

  let displayName;
  if (section === 'users') {
    const u = usersCache.find(u => u.id === id);
    displayName = `"${u.name} (${u.username})"`;
  } else if (section === 'recon') {
    const r = reconCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'ds') {
    const r = dsCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'fields') {
    const r = fieldsCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'rules') {
    const r = rulesCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'rf') {
    const r = rfCache.find(r => r.id === id);
    displayName = `"${r.rule_name} / ${r.field1_name} / ${r.field2_name}"`;
  } else if (section === 'profiles') {
    const r = profilesCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  } else if (section === 'transactions') {
    const r = transactionsCache.find(r => r.id === id);
    displayName = `"${r.name}"`;
  }

  document.getElementById('duplicateItemName').textContent = displayName;
  openModal('duplicateModal');
}

async function confirmDuplicate() {
  const section = state.duplicatingSection;
  const id = state.duplicatingId;

  closeModal('duplicateModal');
  if (section === 'users') await duplicateUser(id);
  else if (section === 'recon') await duplicateRecon(id);
  else if (section === 'ds') await duplicateDs(id);
  else if (section === 'fields') await duplicateField(id);
  else if (section === 'rules') await duplicateRule(id);
  else if (section === 'rf') await duplicateRuleField(id);
  else if (section === 'profiles') await duplicateProfile(id);
  else if (section === 'transactions') await duplicateTransaction(id);
}

// ── RULES ──
let rulesCache = [];
let rulesOptions = { recons: [] };
const rulesState = { pageNum: 1, colName: '', colRecon: '', selectedId: null };

function selectRuleRow(id) {
  rulesState.selectedId = id;
  updateRuleFooterButtons();
}

function updateRuleFooterButtons() {
  const hasSelection = rulesState.selectedId != null;
  ['btnRuleEdit', 'btnRuleDuplicate', 'btnRuleDelete'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerRuleEdit() {
  if (rulesState.selectedId != null) openRuleForm(rulesState.selectedId);
}

function footerRuleDuplicate() {
  if (rulesState.selectedId != null) openDuplicate('rules', rulesState.selectedId);
}

function footerRuleDelete() {
  if (rulesState.selectedId != null) openDelete('rules', rulesState.selectedId);
}

async function loadRules() {
  try {
    rulesCache = await apiFetch('GET', '/api/rule');
    rulesOptions = await apiFetch('GET', '/api/rule/options');
    rulesState.selectedId = null;
    populateRuleFilters();
    renderRules();
  } catch {
    toast('Erro ao carregar regras');
  }
}

function populateRuleFilters() {
  const selName  = document.getElementById('filter-rule-name');
  const selRecon = document.getElementById('filter-rule-recon');
  if (!selName || !selRecon) return;

  const cols = [
    { sel: selName,  vals: [...new Set(rulesCache.map(r => r.name))],       key: 'colName'  },
    { sel: selRecon, vals: [...new Set(rulesCache.map(r => r.recon_name))], key: 'colRecon' },
  ];
  cols.forEach(({ sel, vals, key }) => {
    sel.innerHTML = '<option value="">Todos</option>' +
      vals.sort((a, b) => a.localeCompare(b))
          .map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
    sel.value = rulesState[key];
    rulesState[key] = sel.value;
  });
}

function toggleRuleFilters() {
  const row = document.getElementById('filter-row-rules');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterRulesByColumn();
  }
}

function filterRulesByColumn() {
  rulesState.colName  = document.getElementById('filter-rule-name').value;
  rulesState.colRecon = document.getElementById('filter-rule-recon').value;
  rulesState.pageNum = 1;
  renderRules();
}

function getRulesFiltered() {
  return rulesCache.filter(r =>
    (!rulesState.colName  || r.name        === rulesState.colName)  &&
    (!rulesState.colRecon || r.recon_name  === rulesState.colRecon)
  );
}

function renderRules() {
  const filtered = getRulesFiltered();
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg = Math.min(rulesState.pageNum, totalPages);
  rulesState.pageNum = pg;

  const slice = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody = document.getElementById('tbody-rules');
  const empty = document.getElementById('empty-rules');
  const pag   = document.getElementById('pag-rules');

  syncRowSelection(rulesState, slice);
  updateRuleFooterButtons();

  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  pag.style.display = 'flex';

  tbody.innerHTML = slice.map(r => `
    <tr style="cursor:pointer" onclick="navigateToRuleField(${r.id})">
      <td style="text-align:center" onclick="event.stopPropagation()">
        <input type="radio" name="ruleRowSelect" value="${r.id}" ${rulesState.selectedId === r.id ? 'checked' : ''} onclick="selectRuleRow(${r.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.id}</td>
      <td style="font-size:12.5px">${esc(r.recon_name)}</td>
      <td>${esc(r.name)}</td>
    </tr>
  `).join('');

  const info  = document.getElementById('pag-info-rules');
  const start = (pg - 1) * PAGE_SIZE + 1;
  const end   = Math.min(pg * PAGE_SIZE, total);
  info.textContent = `${start}–${end} de ${total}`;

  const btns = document.getElementById('pag-btns-rules');
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeRulesPage(-1)" ${pg===1?'disabled':''}>&#8249;</button>`;
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoRulesPage(${i})">${i}</button>`;
  }
  html += `<button class="pag-btn" onclick="changeRulesPage(1)" ${pg===totalPages?'disabled':''}>&#8250;</button>`;
  btns.innerHTML = html;
}

function navigateToRuleField(ruleId) {
  window.location.href = `/rule_field?rule_id=${ruleId}`;
}

function changeRulesPage(dir) {
  const total = Math.max(1, Math.ceil(getRulesFiltered().length / PAGE_SIZE));
  rulesState.pageNum = Math.max(1, Math.min(total, rulesState.pageNum + dir));
  renderRules();
}

function gotoRulesPage(n) {
  rulesState.pageNum = n;
  renderRules();
}

function changeRulesPageSize(value) {
  applyPageSize(value);
  rulesState.pageNum = 1;
  renderRules();
}

function openRuleForm(id) {
  if (!state.loggedIn) { openModal('loginModal'); toast('Faça login para continuar'); return; }

  state.editingSection = 'rules';
  state.editingId = id || null;

  document.getElementById('ruleFormTitle').textContent = id ? 'Editar regra' : 'Nova regra';
  clearRuleErrors();

  const selRecon = document.getElementById('ruleFormRecon');
  selRecon.innerHTML = '<option value="">Selecione...</option>' +
    rulesOptions.recons.map(r => `<option value="${r.id}">${esc(r.name)}</option>`).join('');

  const idGroup = document.getElementById('ruleFormIdGroup');
  if (id) {
    const r = rulesCache.find(r => r.id === id);
    idGroup.style.display = '';
    document.getElementById('ruleFormId').value = r.id;
    selRecon.value = r.id_recon || '';
    document.getElementById('ruleFormName').value = r.name;
  } else {
    idGroup.style.display = 'none';
    selRecon.value = '';
    document.getElementById('ruleFormName').value = '';
  }

  openModal('ruleFormModal');
}

async function saveRule() {
  const id_recon = document.getElementById('ruleFormRecon').value;
  const name     = document.getElementById('ruleFormName').value.trim();

  clearRuleErrors();
  let valid = true;
  if (!id_recon) { document.getElementById('errRuleRecon').style.display = 'block'; valid = false; }
  if (!name)     { document.getElementById('errRuleName').style.display  = 'block'; valid = false; }
  if (!valid) return;

  const body = { id_recon: parseInt(id_recon), name };

  try {
    if (state.editingId) {
      await apiFetch('PUT', `/api/rule/${state.editingId}`, body);
      toast('Regra atualizada com sucesso');
    } else {
      await apiFetch('POST', '/api/rule', body);
      toast('Regra criada com sucesso');
    }
    closeModal('ruleFormModal');
    await loadRules();
  } catch (err) {
    if (err.error) {
      const el = document.getElementById('errRuleName');
      el.textContent = err.error;
      el.style.display = 'block';
    } else {
      toast('Erro ao salvar regra');
    }
  }
}

async function duplicateRule(id) {
  try {
    await apiFetch('POST', `/api/rule/${id}/duplicate`);
    toast('Regra duplicada com sucesso');
    await loadRules();
  } catch {
    toast('Erro ao duplicar regra');
  }
}

function clearRuleErrors() {
  document.getElementById('errRuleRecon').style.display = 'none';
  const el = document.getElementById('errRuleName');
  el.style.display = 'none';
  el.textContent = 'Nome é obrigatório';
}

// ── USERS ──
let usersCache = [];
let usersOptions = { profiles: [] };
const usersState = { pageNum: 1, colName: '', colUsername: '', colProfile: '', selectedId: null };

function selectUserRow(id) {
  usersState.selectedId = id;
  updateUserFooterButtons();
}

function updateUserFooterButtons() {
  const hasSelection = usersState.selectedId != null;
  ['btnUserEdit', 'btnUserDuplicate', 'btnUserDelete'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerUserEdit() {
  if (usersState.selectedId != null) openUserForm(usersState.selectedId);
}

function footerUserDuplicate() {
  if (usersState.selectedId != null) openDuplicate('users', usersState.selectedId);
}

function footerUserDelete() {
  if (usersState.selectedId != null) openDelete('users', usersState.selectedId);
}

async function loadUsers() {
  try {
    const [data, options] = await Promise.all([
      apiFetch('GET', '/api/user'),
      apiFetch('GET', '/api/user/options')
    ]);
    usersCache = data;
    usersOptions = options;
    usersState.selectedId = null;
    populateUserFilters();
    renderUsers();
  } catch {
    toast('Erro ao carregar usuários');
  }
}

async function duplicateUser(id) {
  try {
    await apiFetch('POST', `/api/user/${id}/duplicate`);
    toast('Usuário duplicado com sucesso');
    await loadUsers();
  } catch { toast('Erro ao duplicar usuário'); }
}

function populateUserFilters() {
  const selName = document.getElementById('filter-col-name');
  const selUsername = document.getElementById('filter-col-username');
  const selProfile = document.getElementById('filter-col-profile');
  if (!selName || !selUsername || !selProfile) return;

  const names = [...new Set(usersCache.map(u => u.name))].sort((a, b) => a.localeCompare(b));
  const usernames = [...new Set(usersCache.map(u => u.username))].sort((a, b) => a.localeCompare(b));
  const profiles = [...new Set(usersCache.map(u => u.profile_name || ''))].filter(Boolean).sort((a, b) => a.localeCompare(b));

  selName.innerHTML = '<option value="">Todos</option>' +
    names.map(n => `<option value="${esc(n)}">${esc(n)}</option>`).join('');
  selUsername.innerHTML = '<option value="">Todos</option>' +
    usernames.map(u => `<option value="${esc(u)}">${esc(u)}</option>`).join('');
  selProfile.innerHTML = '<option value="">Todos</option>' +
    profiles.map(p => `<option value="${esc(p)}">${esc(p)}</option>`).join('');

  selName.value = usersState.colName;
  selUsername.value = usersState.colUsername;
  selProfile.value = usersState.colProfile;
  usersState.colName = selName.value;
  usersState.colUsername = selUsername.value;
  usersState.colProfile = selProfile.value;
}

function toggleUserFilters() {
  const row = document.getElementById('filter-row-users');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterUsersByColumn();
  }
}

function filterUsersByColumn() {
  usersState.colName = document.getElementById('filter-col-name').value;
  usersState.colUsername = document.getElementById('filter-col-username').value;
  usersState.colProfile = document.getElementById('filter-col-profile').value;
  usersState.pageNum = 1;
  renderUsers();
}

function getUsersFiltered() {
  return usersCache.filter(u =>
    (!usersState.colName || u.name === usersState.colName) &&
    (!usersState.colUsername || u.username === usersState.colUsername) &&
    (!usersState.colProfile || u.profile_name === usersState.colProfile)
  );
}

function renderUsers() {
  const filtered = getUsersFiltered();
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg = Math.min(usersState.pageNum, totalPages);
  usersState.pageNum = pg;

  const slice = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody = document.getElementById('tbody-users');
  const empty = document.getElementById('empty-users');
  const pag = document.getElementById('pag-users');

  syncRowSelection(usersState, slice);
  updateUserFooterButtons();

  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  pag.style.display = 'flex';

  tbody.innerHTML = slice.map(u => `
    <tr>
      <td style="text-align:center">
        <input type="radio" name="userRowSelect" value="${u.id}" ${usersState.selectedId === u.id ? 'checked' : ''} onclick="selectUserRow(${u.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${u.id}</td>
      <td style="color:var(--gray-400);font-size:12.5px">${esc(u.profile_name || '-')}</td>
      <td>${esc(u.name)}</td>
      <td style="color:var(--gray-400);font-size:12.5px">${esc(u.username)}</td>
    </tr>
  `).join('');

  const info = document.getElementById('pag-info-users');
  const start = (pg - 1) * PAGE_SIZE + 1;
  const end = Math.min(pg * PAGE_SIZE, total);
  info.textContent = `${start}–${end} de ${total}`;

  const btns = document.getElementById('pag-btns-users');
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeUsersPage(-1)" ${pg===1?'disabled':''}>‹</button>`;
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoUsersPage(${i})">${i}</button>`;
  }
  html += `<button class="pag-btn" onclick="changeUsersPage(1)" ${pg===totalPages?'disabled':''}>›</button>`;
  btns.innerHTML = html;
}

function changeUsersPage(dir) {
  const total = Math.max(1, Math.ceil(getUsersFiltered().length / PAGE_SIZE));
  usersState.pageNum = Math.max(1, Math.min(total, usersState.pageNum + dir));
  renderUsers();
}

function gotoUsersPage(n) {
  usersState.pageNum = n;
  renderUsers();
}

function changeUsersPageSize(value) {
  applyPageSize(value);
  usersState.pageNum = 1;
  renderUsers();
}

function _populateUserDropdowns() {
  document.getElementById('userFormProfile').innerHTML =
    '<option value="">Selecione...</option>' +
    usersOptions.profiles.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
}

function openUserForm(id) {
  if (!state.loggedIn) { openModal('loginModal'); toast('Faça login para continuar'); return; }

  state.editingSection = 'users';
  state.editingId = id || null;

  document.getElementById('userFormTitle').textContent = id ? 'Editar usuário' : 'Novo usuário';
  clearUserErrors();
  _populateUserDropdowns();

  const idGroup = document.getElementById('userFormIdGroup');
  if (id) {
    const u = usersCache.find(u => u.id === id);
    idGroup.style.display = '';
    document.getElementById('userFormId').value = u.id;
    document.getElementById('userFormName').value = u.name;
    document.getElementById('userFormUsername').value = u.username;
    document.getElementById('userFormPassword').value = '';
    document.getElementById('userFormProfile').value = u.id_profile || '';
    document.getElementById('userPasswordLabel').textContent = 'Nova senha (deixe em branco para manter)';
  } else {
    idGroup.style.display = 'none';
    document.getElementById('userFormName').value = '';
    document.getElementById('userFormUsername').value = '';
    document.getElementById('userFormPassword').value = '';
    document.getElementById('userFormProfile').value = '';
    document.getElementById('userPasswordLabel').textContent = 'Senha';
  }

  openModal('userFormModal');
}

async function saveUser() {
  const name = document.getElementById('userFormName').value.trim();
  const username = document.getElementById('userFormUsername').value.trim();
  const password = document.getElementById('userFormPassword').value;
  const id_profile = document.getElementById('userFormProfile').value || null;

  clearUserErrors();
  let valid = true;
  if (!name) { document.getElementById('errUserName').style.display = 'block'; valid = false; }
  if (!username) { document.getElementById('errUserUsername').style.display = 'block'; valid = false; }
  if (!id_profile) { document.getElementById('errUserProfile').style.display = 'block'; valid = false; }
  if (!state.editingId && !password) { document.getElementById('errUserPassword').style.display = 'block'; valid = false; }
  if (!valid) return;

  const body = { name, username, id_profile };
  if (password) body.password = password;

  try {
    if (state.editingId) {
      await apiFetch('PUT', `/api/user/${state.editingId}`, body);
      toast('Usuário atualizado com sucesso');
    } else {
      await apiFetch('POST', '/api/user', body);
      toast('Usuário criado com sucesso');
    }
    closeModal('userFormModal');
    await loadUsers();
  } catch (err) {
    if (err.error) {
      const el = document.getElementById(err.error.includes('Perfil') ? 'errUserProfile' : 'errUserUsername');
      el.textContent = err.error;
      el.style.display = 'block';
    } else {
      toast('Erro ao salvar usuário');
    }
  }
}

function clearUserErrors() {
  document.getElementById('errUserName').style.display = 'none';
  const elUsername = document.getElementById('errUserUsername');
  elUsername.style.display = 'none';
  elUsername.textContent = 'Usuário é obrigatório';
  document.getElementById('errUserPassword').style.display = 'none';
  document.getElementById('errUserProfile').style.display = 'none';
}

// ── FIELDS ──
let fieldsCache = [];
let fieldsOptions = { datasources: [], field_types: [] };
const fieldsState = { pageNum: 1, colName: '', colDs: '', colRecon: '', colPos: '', colType: '', selectedId: null };

function selectFieldRow(id) {
  fieldsState.selectedId = id;
  updateFieldFooterButtons();
}

function updateFieldFooterButtons() {
  const hasSelection = fieldsState.selectedId != null;
  ['btnFieldEdit', 'btnFieldDuplicate', 'btnFieldDelete'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerFieldEdit() {
  if (fieldsState.selectedId != null) openFieldForm(fieldsState.selectedId);
}

function footerFieldDuplicate() {
  if (fieldsState.selectedId != null) openDuplicate('fields', fieldsState.selectedId);
}

function footerFieldDelete() {
  if (fieldsState.selectedId != null) openDelete('fields', fieldsState.selectedId);
}

async function loadFields() {
  try {
    fieldsCache = await apiFetch('GET', '/api/field');
    fieldsOptions = await apiFetch('GET', '/api/field/options');
    fieldsState.selectedId = null;
    populateFieldFilters();

    const dsIdParam = new URLSearchParams(location.search).get('ds_id');
    if (dsIdParam) {
      const ds = fieldsOptions.datasources.find(d => String(d.id) === dsIdParam);
      if (ds) {
        fieldsState.colDs = ds.name;
        const sel = document.getElementById('filter-field-ds');
        if (sel) sel.value = ds.name;
      }
    }

    renderFields();
  } catch {
    toast('Erro ao carregar campos');
  }
}

function populateFieldFilters() {
  const ids = ['filter-field-recon', 'filter-field-ds', 'filter-field-pos', 'filter-field-name', 'filter-field-type'];
  if (!document.getElementById(ids[0])) return;

  const cols = [
    { id: ids[0], vals: [...new Set(fieldsCache.map(r => r.recon_name))],     key: 'colRecon' },
    { id: ids[1], vals: [...new Set(fieldsCache.map(r => r.ds_name))],        key: 'colDs'   },
    { id: ids[2], vals: [...new Set(fieldsCache.map(r => String(r.position)))], key: 'colPos'  },
    { id: ids[3], vals: [...new Set(fieldsCache.map(r => r.name))],           key: 'colName' },
    { id: ids[4], vals: [...new Set(fieldsCache.map(r => r.field_type_name))], key: 'colType' },
  ];

  cols.forEach(({ id, vals, key }) => {
    const sel = document.getElementById(id);
    sel.innerHTML = '<option value="">Todos</option>' +
      vals.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
          .map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
    sel.value = fieldsState[key];
    fieldsState[key] = sel.value;
  });
}

function toggleFieldFilters() {
  const row = document.getElementById('filter-row-fields');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterFieldsByColumn();
  }
}

function filterFieldsByColumn() {
  fieldsState.colRecon = document.getElementById('filter-field-recon').value;
  fieldsState.colName = document.getElementById('filter-field-name').value;
  fieldsState.colDs   = document.getElementById('filter-field-ds').value;
  fieldsState.colPos  = document.getElementById('filter-field-pos').value;
  fieldsState.colType = document.getElementById('filter-field-type').value;
  fieldsState.pageNum = 1;
  renderFields();
}

function getFieldsFiltered() {
  return fieldsCache.filter(r =>
    (!fieldsState.colRecon || r.recon_name             === fieldsState.colRecon) &&
    (!fieldsState.colName || r.name                    === fieldsState.colName) &&
    (!fieldsState.colDs   || r.ds_name                 === fieldsState.colDs)   &&
    (!fieldsState.colPos  || String(r.position)        === fieldsState.colPos)  &&
    (!fieldsState.colType || r.field_type_name         === fieldsState.colType)
  );
}

function renderFields() {
  const filtered = getFieldsFiltered();
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg = Math.min(fieldsState.pageNum, totalPages);
  fieldsState.pageNum = pg;

  const slice = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody = document.getElementById('tbody-fields');
  const empty = document.getElementById('empty-fields');
  const pag = document.getElementById('pag-fields');

  syncRowSelection(fieldsState, slice);
  updateFieldFooterButtons();

  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  pag.style.display = 'flex';

  tbody.innerHTML = slice.map(r => `
    <tr>
      <td style="text-align:center">
        <input type="radio" name="fieldRowSelect" value="${r.id}" ${fieldsState.selectedId === r.id ? 'checked' : ''} onclick="selectFieldRow(${r.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.id}</td>
      <td style="font-size:12.5px">${esc(r.recon_name)}</td>
      <td style="font-size:12.5px">${esc(r.ds_name)}</td>
      <td style="color:var(--gray-400);font-size:12.5px;text-align:center">${r.position}</td>
      <td>${esc(r.name)}</td>
      <td style="color:var(--gray-400);font-size:12.5px">${esc(r.field_type_name)}</td>
    </tr>
  `).join('');

  const info = document.getElementById('pag-info-fields');
  const start = (pg - 1) * PAGE_SIZE + 1;
  const end = Math.min(pg * PAGE_SIZE, total);
  info.textContent = `${start}–${end} de ${total}`;

  const btns = document.getElementById('pag-btns-fields');
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeFieldsPage(-1)" ${pg===1?'disabled':''}>&#8249;</button>`;
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoFieldsPage(${i})">${i}</button>`;
  }
  html += `<button class="pag-btn" onclick="changeFieldsPage(1)" ${pg===totalPages?'disabled':''}>&#8250;</button>`;
  btns.innerHTML = html;
}

function changeFieldsPage(dir) {
  const total = Math.max(1, Math.ceil(getFieldsFiltered().length / PAGE_SIZE));
  fieldsState.pageNum = Math.max(1, Math.min(total, fieldsState.pageNum + dir));
  renderFields();
}

function gotoFieldsPage(n) {
  fieldsState.pageNum = n;
  renderFields();
}

function changeFieldsPageSize(value) {
  applyPageSize(value);
  fieldsState.pageNum = 1;
  renderFields();
}

function _populateFieldsDropdowns() {
  document.getElementById('fieldFormDs').innerHTML =
    '<option value="">Selecione...</option>' +
    fieldsOptions.datasources.map(d =>
      `<option value="${d.id}">${esc(d.recon_name)} / ${esc(d.name)}</option>`
    ).join('');
  document.getElementById('fieldFormType').innerHTML =
    '<option value="">Selecione...</option>' +
    fieldsOptions.field_types.map(t =>
      `<option value="${t.id}">${esc(t.name)}</option>`
    ).join('');
}

function openFieldForm(id) {
  if (!state.loggedIn) { openModal('loginModal'); toast('Faça login para continuar'); return; }

  state.editingSection = 'fields';
  state.editingId = id || null;

  document.getElementById('fieldFormTitle').textContent = id ? 'Editar campo' : 'Novo campo';
  clearFieldErrors();
  _populateFieldsDropdowns();

  const posInput = document.getElementById('fieldFormPosition');
  const idGroup = document.getElementById('fieldFormIdGroup');

  if (id) {
    const r = fieldsCache.find(r => r.id === id);
    idGroup.style.display = '';
    document.getElementById('fieldFormId').value = r.id;
    posInput.disabled = false;
    document.getElementById('fieldFormDs').value = r.id_ds || '';
    posInput.value = r.position;
    document.getElementById('fieldFormName').value = r.name;
    document.getElementById('fieldFormType').value = r.id_field_type || '';
    document.getElementById('fieldFormValue').value = r.value || '';
  } else {
    idGroup.style.display = 'none';
    document.getElementById('fieldFormDs').value = '';
    posInput.value = '';
    posInput.disabled = true;
    document.getElementById('fieldFormName').value = '';
    document.getElementById('fieldFormType').value = '';
    document.getElementById('fieldFormValue').value = '';
  }

  openModal('fieldFormModal');
}

function onFieldFormDsChange() {
  if (state.editingId) return;
  const idDs = document.getElementById('fieldFormDs').value;
  const posInput = document.getElementById('fieldFormPosition');
  if (!idDs) {
    posInput.value = '';
    return;
  }
  const maxPos = fieldsCache
    .filter(f => String(f.id_ds) === String(idDs))
    .reduce((max, f) => Math.max(max, Number(f.position) || 0), 0);
  posInput.value = maxPos + 1;
}

async function saveField() {
  const id_ds = document.getElementById('fieldFormDs').value;
  const position = document.getElementById('fieldFormPosition').value;
  const name = document.getElementById('fieldFormName').value.trim();
  const id_field_type = document.getElementById('fieldFormType').value || null;
  const value = document.getElementById('fieldFormValue').value.trim();

  clearFieldErrors();
  let valid = true;
  const posNum = parseInt(position, 10);
  if (!id_ds) { document.getElementById('errFieldDs').style.display = 'block'; valid = false; }
  if (!position || isNaN(posNum) || posNum < 1) {
    const el = document.getElementById('errFieldPosition');
    el.textContent = posNum < 1 ? 'Posição deve ser maior que zero' : 'Posição é obrigatória';
    el.style.display = 'block';
    valid = false;
  }
  if (!name) { document.getElementById('errFieldName').style.display = 'block'; valid = false; }
  if (!id_field_type) { document.getElementById('errFieldType').style.display = 'block'; valid = false; }
  if (!valid) return;

  const body = {
    id_ds: parseInt(id_ds),
    position: posNum,
    name,
    id_field_type: id_field_type ? parseInt(id_field_type) : null,
    value
  };

  try {
    if (state.editingId) {
      await apiFetch('PUT', `/api/field/${state.editingId}`, body);
      toast('Campo atualizado com sucesso');
    } else {
      await apiFetch('POST', '/api/field', body);
      toast('Campo criado com sucesso');
    }
    closeModal('fieldFormModal');
    await loadFields();
  } catch (err) {
    if (err.error) {
      const el = document.getElementById('errFieldPosition');
      el.textContent = err.error;
      el.style.display = 'block';
    } else {
      toast('Erro ao salvar campo');
    }
  }
}

async function duplicateField(id) {
  try {
    await apiFetch('POST', `/api/field/${id}/duplicate`);
    toast('Campo duplicado com sucesso');
    await loadFields();
  } catch {
    toast('Erro ao duplicar campo');
  }
}

function clearFieldErrors() {
  document.getElementById('errFieldDs').style.display = 'none';
  const elPos = document.getElementById('errFieldPosition');
  elPos.style.display = 'none';
  elPos.textContent = 'Posição é obrigatória';
  const elName = document.getElementById('errFieldName');
  elName.style.display = 'none';
  elName.textContent = 'Nome é obrigatório';
  document.getElementById('errFieldType').style.display = 'none';
}

// ── DATASOURCE ──
let dsCache = [];
let dsOptions = { recons: [], sides: [], ds_types: [] };
const dsState = {
  pageNum: 1,
  colName: '',
  colRecon: '',
  colSide: '',
  colType: '',
  colCredentials: '',
  colQuery: '',
  colFilename: '',
  colUrl: '',
  selectedId: null
};

function selectDsRow(id) {
  dsState.selectedId = id;
  updateDsFooterButtons();
}

function updateDsFooterButtons() {
  const hasSelection = dsState.selectedId != null;
  ['btnDsEdit', 'btnDsDuplicate', 'btnDsDelete'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerDsEdit() {
  if (dsState.selectedId != null) openDsForm(dsState.selectedId);
}

function footerDsDuplicate() {
  if (dsState.selectedId != null) openDuplicate('ds', dsState.selectedId);
}

function footerDsDelete() {
  if (dsState.selectedId != null) openDelete('ds', dsState.selectedId);
}

async function loadDatasource() {
  try {
    if (!state.loggedIn) {
      await checkSession();
    }
    if (!state.loggedIn) {
      openModal('loginModal');
      toast('Faça login para continuar');
      return;
    }

    const [data, options] = await Promise.all([
      apiFetch('GET', '/api/ds'),
      apiFetch('GET', '/api/ds/options')
    ]);

    dsCache = data;
    dsOptions = options;
    dsState.selectedId = null;
    populateDsFilters();

    const reconIdParam = new URLSearchParams(location.search).get('recon_id');
    if (reconIdParam) {
      const recon = dsOptions.recons.find(r => String(r.id) === reconIdParam);
      if (recon) {
        dsState.colRecon = recon.name;
        const sel = document.getElementById('filter-ds-recon');
        if (sel) sel.value = recon.name;
      }
    }

    renderDatasource();
  } catch (err) {
    if (err && err.error === 'Não autenticado') {
      openModal('loginModal');
      toast('Faça login para continuar');
      return;
    }
    toast('Erro ao carregar fontes de dados');
  }
}

function populateDsFilters() {
  const ids = [
    'filter-ds-name',
    'filter-ds-recon',
    'filter-ds-side',
    'filter-ds-type',
    'filter-ds-credentials',
    'filter-ds-query',
    'filter-ds-filename',
    'filter-ds-url'
  ];
  if (!document.getElementById(ids[0])) return;

  const cols = [
    { id: ids[0], vals: [...new Set(dsCache.map(r => r.name))],                key: 'colName'       },
    { id: ids[1], vals: [...new Set(dsCache.map(r => r.recon_name))],           key: 'colRecon'      },
    { id: ids[2], vals: [...new Set(dsCache.map(r => r.side_name))],            key: 'colSide'       },
    { id: ids[3], vals: [...new Set(dsCache.map(r => r.ds_type_name))],         key: 'colType'       },
    { id: ids[4], vals: [...new Set(dsCache.map(r => r.credentials || ''))].filter(Boolean), key: 'colCredentials' },
    { id: ids[5], vals: [...new Set(dsCache.map(r => r.query || ''))].filter(Boolean), key: 'colQuery' },
    { id: ids[6], vals: [...new Set(dsCache.map(r => r.filename || ''))].filter(Boolean), key: 'colFilename' },
    { id: ids[7], vals: [...new Set(dsCache.map(r => r.url || ''))].filter(Boolean), key: 'colUrl' }
  ];

  cols.forEach(({ id, vals, key }) => {
    const sel = document.getElementById(id);
    sel.innerHTML = '<option value="">Todos</option>' +
      vals.sort((a, b) => a.localeCompare(b))
          .map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
    sel.value = dsState[key];
    dsState[key] = sel.value;
  });
}

function toggleDsFilters() {
  const row = document.getElementById('filter-row-ds');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterDsByColumn();
  }
}

function filterDsByColumn() {
  dsState.colName       = document.getElementById('filter-ds-name').value;
  dsState.colRecon      = document.getElementById('filter-ds-recon').value;
  dsState.colSide       = document.getElementById('filter-ds-side').value;
  dsState.colType       = document.getElementById('filter-ds-type').value;
  dsState.colCredentials = document.getElementById('filter-ds-credentials').value;
  dsState.colQuery      = document.getElementById('filter-ds-query').value;
  dsState.colFilename   = document.getElementById('filter-ds-filename').value;
  dsState.colUrl        = document.getElementById('filter-ds-url').value;
  dsState.pageNum = 1;
  renderDatasource();
}

function getDsFiltered() {
  return dsCache.filter(r =>
    (!dsState.colName       || r.name               === dsState.colName)       &&
    (!dsState.colRecon      || r.recon_name         === dsState.colRecon)      &&
    (!dsState.colSide       || r.side_name          === dsState.colSide)       &&
    (!dsState.colType        || r.ds_type_name       === dsState.colType)       &&
    (!dsState.colCredentials || r.credentials        === dsState.colCredentials) &&
    (!dsState.colQuery       || r.query              === dsState.colQuery)      &&
    (!dsState.colFilename   || r.filename           === dsState.colFilename)   &&
    (!dsState.colUrl        || r.url                === dsState.colUrl)
  );
}

function shortText(value, max = 60) {
  const text = value || '';
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

function renderDatasource() {
  const filtered = getDsFiltered();
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg = Math.min(dsState.pageNum, totalPages);
  dsState.pageNum = pg;

  const slice = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody = document.getElementById('tbody-ds');
  const empty = document.getElementById('empty-ds');
  const pag = document.getElementById('pag-ds');

  syncRowSelection(dsState, slice);
  updateDsFooterButtons();

  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  pag.style.display = 'flex';

  tbody.innerHTML = slice.map(r => `
    <tr style="cursor:pointer" onclick="navigateToFields(${r.id})">
      <td style="text-align:center" onclick="event.stopPropagation()">
        <input type="radio" name="dsRowSelect" value="${r.id}" ${dsState.selectedId === r.id ? 'checked' : ''} onclick="selectDsRow(${r.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.id}</td>
      <td style="font-size:12.5px">${esc(r.recon_name)}</td>
      <td>${esc(r.name)}</td>
      <td style="color:var(--gray-400);font-size:12.5px">${esc(r.side_name)}</td>
      <td style="color:var(--gray-400);font-size:12.5px">${esc(r.ds_type_name)}</td>
      <td title="${esc(r.credentials || '')}" style="font-size:12.5px">${esc(shortText(r.credentials, 50) || '-')}</td>
      <td title="${esc(r.query || '')}" style="font-size:12.5px">${esc(shortText(r.query, 80) || '-')}</td>
      <td style="font-size:12.5px">${esc(r.filename || '-')}</td>
      <td style="font-size:12.5px">${esc(r.url || '-')}</td>
    </tr>
  `).join('');

  const info = document.getElementById('pag-info-ds');
  const start = (pg - 1) * PAGE_SIZE + 1;
  const end = Math.min(pg * PAGE_SIZE, total);
  info.textContent = `${start}–${end} de ${total}`;

  const btns = document.getElementById('pag-btns-ds');
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeDsPage(-1)" ${pg===1?'disabled':''}>&#8249;</button>`;
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoDsPage(${i})">${i}</button>`;
  }
  html += `<button class="pag-btn" onclick="changeDsPage(1)" ${pg===totalPages?'disabled':''}>&#8250;</button>`;
  btns.innerHTML = html;
}

function navigateToFields(dsId) {
  window.location.href = `/field?ds_id=${dsId}`;
}

function changeDsPage(dir) {
  const total = Math.max(1, Math.ceil(getDsFiltered().length / PAGE_SIZE));
  dsState.pageNum = Math.max(1, Math.min(total, dsState.pageNum + dir));
  renderDatasource();
}

function gotoDsPage(n) {
  dsState.pageNum = n;
  renderDatasource();
}

function changeDsPageSize(value) {
  applyPageSize(value);
  dsState.pageNum = 1;
  renderDatasource();
}

function _populateDsDropdowns() {
  document.getElementById('dsFormRecon').innerHTML =
    '<option value="">Selecione...</option>' +
    dsOptions.recons.map(r => `<option value="${r.id}">${esc(r.name)}</option>`).join('');
  document.getElementById('dsFormSide').innerHTML =
    '<option value="">Selecione...</option>' +
    dsOptions.sides.map(s => `<option value="${s.id}">${esc(s.name)}</option>`).join('');
  document.getElementById('dsFormType').innerHTML =
    '<option value="">Selecione...</option>' +
    dsOptions.ds_types.map(t => `<option value="${t.id}">${esc(t.name)}</option>`).join('');
  document.getElementById('dsFormType').addEventListener('change', updateDsFieldVisibility);
}

function updateDsFieldVisibility() {
  const typeValue = document.getElementById('dsFormType')?.value;
  const typeId = typeValue ? parseInt(typeValue, 10) : null;

  const hideConnectionFields = typeId === 1 || typeId === 2;
  const hideFileFields = typeId !== 1 && typeId !== 2;
  const hideUrlForType1 = typeId === 1;
  const hideType2SpecificFields = typeId === 2;
  const showTestButton = typeId !== null && typeId > 2;

  const connectionGroup = document.getElementById('dsFormCredentials')?.closest('.form-group');
  const queryGroup = document.getElementById('dsFormQuery')?.closest('.form-group');
  const filenameGroup = document.getElementById('dsFormFilename')?.closest('.form-group');
  const delimiterGroup = document.getElementById('dsFormDelimiter')?.closest('.form-group');
  const urlGroup = document.getElementById('dsFormUrl')?.closest('.form-group');
  const testButton = document.getElementById('btnTestConnection');

  if (connectionGroup) connectionGroup.style.display = (hideConnectionFields || hideType2SpecificFields) ? 'none' : '';
  if (queryGroup) queryGroup.style.display = (hideConnectionFields || hideType2SpecificFields) ? 'none' : '';
  if (filenameGroup) filenameGroup.style.display = (hideFileFields || hideType2SpecificFields) ? 'none' : '';
  if (delimiterGroup) delimiterGroup.style.display = (hideFileFields || hideType2SpecificFields) ? 'none' : '';
  if (urlGroup) urlGroup.style.display = (hideFileFields || hideUrlForType1) ? 'none' : '';
  if (testButton) testButton.style.display = showTestButton ? '' : 'none';
}

function openDsForm(id) {
  if (!state.loggedIn) { openModal('loginModal'); toast('Faça login para continuar'); return; }

  state.editingSection = 'ds';
  state.editingId = id || null;

  document.getElementById('dsFormTitle').textContent = id ? 'Editar fonte de dados' : 'Nova fonte de dados';
  clearDsErrors();
  _populateDsDropdowns();

  const idGroup = document.getElementById('dsFormIdGroup');
  if (id) {
    const r = dsCache.find(r => r.id === id);
    idGroup.style.display = '';
    document.getElementById('dsFormId').value = r.id;
    document.getElementById('dsFormName').value = r.name;
    document.getElementById('dsFormRecon').value = r.id_recon || '';
    document.getElementById('dsFormSide').value = r.id_side || '';
    document.getElementById('dsFormType').value = r.id_type || '';
    document.getElementById('dsFormCredentials').value = r.credentials || '';
    document.getElementById('dsFormQuery').value = r.query || '';
    document.getElementById('dsFormFilename').value = r.filename || '';
    document.getElementById('dsFormDelimiter').value = r.delimiter || '';
    document.getElementById('dsFormUrl').value = r.url || '';
  } else {
    idGroup.style.display = 'none';
    document.getElementById('dsFormName').value = '';
    document.getElementById('dsFormRecon').value = '';
    document.getElementById('dsFormSide').value = '';
    document.getElementById('dsFormType').value = '';
    document.getElementById('dsFormCredentials').value = '';
    document.getElementById('dsFormQuery').value = '';
    document.getElementById('dsFormFilename').value = '';
    document.getElementById('dsFormDelimiter').value = '';
    document.getElementById('dsFormUrl').value = '';
  }

  updateDsFieldVisibility();
  openModal('dsFormModal');
}

async function saveDs() {
  const name = document.getElementById('dsFormName').value.trim();
  const id_recon = document.getElementById('dsFormRecon').value;
  const id_side = document.getElementById('dsFormSide').value || null;
  const id_type = document.getElementById('dsFormType').value || null;
  const credentials = document.getElementById('dsFormCredentials').value.trim();
  const query = document.getElementById('dsFormQuery').value.trim();
  const filename = document.getElementById('dsFormFilename').value.trim();
  const delimiter = document.getElementById('dsFormDelimiter').value.trim();
  const url = document.getElementById('dsFormUrl').value.trim();

  clearDsErrors();
  let valid = true;
  const typeId = id_type ? parseInt(id_type, 10) : null;
  if (!name) { document.getElementById('errDsName').style.display = 'block'; valid = false; }
  if (!id_recon) { document.getElementById('errDsRecon').style.display = 'block'; valid = false; }
  if (!id_side) { document.getElementById('errDsSide').style.display = 'block'; valid = false; }
  if (!typeId) { document.getElementById('errDsType').style.display = 'block'; valid = false; }
  if (typeId === 1) {
    if (!filename)  { document.getElementById('errDsFilename').style.display  = 'block'; valid = false; }
    if (!delimiter) { document.getElementById('errDsDelimiter').style.display = 'block'; valid = false; }
  } else if (typeId === 2) {
    if (!url) { document.getElementById('errDsUrl').style.display = 'block'; valid = false; }
  } else if (typeId) {
    if (!credentials) { document.getElementById('errDsCredentials').style.display = 'block'; valid = false; }
    if (!query)       { document.getElementById('errDsQuery').style.display       = 'block'; valid = false; }
  }
  if (!valid) return;

  const body = {
    name,
    id_recon: parseInt(id_recon),
    id_side: id_side ? parseInt(id_side) : null,
    id_type: id_type ? parseInt(id_type) : null,
    credentials,
    query,
    filename,
    delimiter,
    url
  };

  try {
    if (state.editingId) {
      await apiFetch('PUT', `/api/ds/${state.editingId}`, body);
      toast('Fonte de dados atualizada com sucesso');
    } else {
      await apiFetch('POST', '/api/ds', body);
      toast('Fonte de dados criada com sucesso');
    }
    closeModal('dsFormModal');
    await loadDatasource();
  } catch (err) {
    if (err.error) {
      const el = document.getElementById('errDsName');
      el.textContent = err.error;
      el.style.display = 'block';
    } else {
      toast('Erro ao salvar fonte de dados');
    }
  }
}

async function testDsConnection() {
  const typeValue = document.getElementById('dsFormType').value;
  const credentials = document.getElementById('dsFormCredentials').value.trim();
  const query = document.getElementById('dsFormQuery').value.trim();
  const id_type = typeValue ? parseInt(typeValue, 10) : null;

  if (!id_type || !credentials) {
    toast('Preencha Tipo e Credenciais para testar a conexão');
    return;
  }

  if (id_type !== 2 && !query) {
    toast('Preencha a Query para testar a conexão');
    return;
  }

  try {
    const payload = {
      id_type,
      credentials
    };
    if (query) payload.query = query;

    const res = await apiFetch('POST', '/api/ds/test', payload);
    toast(res.message || 'Conexão testada com sucesso');
  } catch (err) {
    toast(err.error || 'Erro ao testar conexão');
  }
}

async function duplicateDs(id) {
  try {
    await apiFetch('POST', `/api/ds/${id}/duplicate`);
    toast('Fonte de dados duplicada com sucesso');
    await loadDatasource();
  } catch {
    toast('Erro ao duplicar fonte de dados');
  }
}

function clearDsErrors() {
  const elName = document.getElementById('errDsName');
  elName.style.display = 'none';
  elName.textContent = 'Nome é obrigatório';
  ['errDsRecon', 'errDsSide', 'errDsType', 'errDsCredentials', 'errDsQuery', 'errDsFilename', 'errDsDelimiter', 'errDsUrl']
    .forEach(id => { document.getElementById(id).style.display = 'none'; });
}

// ── RECON ──
let reconCache = [];
const reconState = { pageNum: 1, colName: '', colDesc: '', selectedId: null };

function selectReconRow(id) {
  reconState.selectedId = id;
  updateReconFooterButtons();
}

function updateReconFooterButtons() {
  const hasSelection = reconState.selectedId != null;
  ['btnReconEdit', 'btnReconDuplicate', 'btnReconDelete', 'btnReconExport'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerReconEdit() {
  if (reconState.selectedId != null) openReconForm(reconState.selectedId);
}

function footerReconDuplicate() {
  if (reconState.selectedId != null) openDuplicate('recon', reconState.selectedId);
}

function footerReconDelete() {
  if (reconState.selectedId != null) openDelete('recon', reconState.selectedId);
}

function footerReconExport() {
  if (reconState.selectedId != null) exportRecon(reconState.selectedId);
}

async function loadRecon() {
  try {
    reconCache = await apiFetch('GET', '/api/recon');
    reconState.selectedId = null;
    populateReconFilters();
    renderRecon();
  } catch {
    toast('Erro ao carregar conciliações');
  }
}

function populateReconFilters() {
  const selName = document.getElementById('filter-recon-name');
  const selDesc = document.getElementById('filter-recon-desc');
  if (!selName || !selDesc) return;

  const cols = [
    { sel: selName, vals: [...new Set(reconCache.map(r => r.name))],        key: 'colName' },
    { sel: selDesc, vals: [...new Set(reconCache.map(r => r.description))], key: 'colDesc' },
  ];

  cols.forEach(({ sel, vals, key }) => {
    sel.innerHTML = '<option value="">Todos</option>' +
      vals.sort((a, b) => a.localeCompare(b))
          .map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
    sel.value = reconState[key];
    reconState[key] = sel.value;
  });
}

function toggleReconFilters() {
  const row = document.getElementById('filter-row-recon');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterReconByColumn();
  }
}

function filterReconByColumn() {
  reconState.colName = document.getElementById('filter-recon-name').value;
  reconState.colDesc = document.getElementById('filter-recon-desc').value;
  reconState.pageNum = 1;
  renderRecon();
}

function getReconFiltered() {
  return reconCache.filter(r =>
    (!reconState.colName || r.name        === reconState.colName) &&
    (!reconState.colDesc || r.description === reconState.colDesc)
  );
}

function renderRecon() {
  const filtered = getReconFiltered();
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg = Math.min(reconState.pageNum, totalPages);
  reconState.pageNum = pg;

  const slice = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody = document.getElementById('tbody-recon');
  const empty = document.getElementById('empty-recon');
  const pag = document.getElementById('pag-recon');

  syncRowSelection(reconState, slice);
  updateReconFooterButtons();

  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  pag.style.display = 'flex';

  tbody.innerHTML = slice.map(r => {
    const desc = r.description || '';
    const descDisplay = desc.length > 80 ? desc.slice(0, 80) + '…' : desc;
    return `
    <tr style="cursor:pointer" onclick="navigateToDs(${r.id})">
      <td style="text-align:center" onclick="event.stopPropagation()">
        <input type="radio" name="reconRowSelect" value="${r.id}" ${reconState.selectedId === r.id ? 'checked' : ''} onclick="selectReconRow(${r.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.id}</td>
      <td>${esc(r.name)}</td>
      <td style="color:var(--gray-400);font-size:12.5px">${esc(descDisplay)}</td>
    </tr>`;
  }).join('');

  const info = document.getElementById('pag-info-recon');
  const start = (pg - 1) * PAGE_SIZE + 1;
  const end = Math.min(pg * PAGE_SIZE, total);
  info.textContent = `${start}–${end} de ${total}`;

  const btns = document.getElementById('pag-btns-recon');
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeReconPage(-1)" ${pg===1?'disabled':''}>&#8249;</button>`;
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoReconPage(${i})">${i}</button>`;
  }
  html += `<button class="pag-btn" onclick="changeReconPage(1)" ${pg===totalPages?'disabled':''}>&#8250;</button>`;
  btns.innerHTML = html;
}

function navigateToDs(reconId) {
  window.location.href = `/ds?recon_id=${reconId}`;
}

function changeReconPage(dir) {
  const total = Math.max(1, Math.ceil(getReconFiltered().length / PAGE_SIZE));
  reconState.pageNum = Math.max(1, Math.min(total, reconState.pageNum + dir));
  renderRecon();
}

function gotoReconPage(n) {
  reconState.pageNum = n;
  renderRecon();
}

function changeReconPageSize(value) {
  applyPageSize(value);
  reconState.pageNum = 1;
  renderRecon();
}

function openReconForm(id) {
  if (!state.loggedIn) { openModal('loginModal'); toast('Faça login para continuar'); return; }

  state.editingSection = 'recon';
  state.editingId = id || null;

  document.getElementById('reconFormTitle').textContent = id ? 'Editar conciliação' : 'Nova conciliação';
  clearReconErrors();

  const idGroup = document.getElementById('reconFormIdGroup');
  if (id) {
    const r = reconCache.find(r => r.id === id);
    idGroup.style.display = '';
    document.getElementById('reconFormId').value = r.id;
    document.getElementById('reconFormName').value = r.name;
    document.getElementById('reconFormDescription').value = r.description || '';
  } else {
    idGroup.style.display = 'none';
    document.getElementById('reconFormName').value = '';
    document.getElementById('reconFormDescription').value = '';
  }

  openModal('reconFormModal');
}

async function saveRecon() {
  const name = document.getElementById('reconFormName').value.trim();
  const description = document.getElementById('reconFormDescription').value.trim();

  clearReconErrors();
  if (!name) { document.getElementById('errReconName').style.display = 'block'; return; }

  try {
    if (state.editingId) {
      await apiFetch('PUT', `/api/recon/${state.editingId}`, { name, description });
      toast('Conciliação atualizada com sucesso');
    } else {
      await apiFetch('POST', '/api/recon', { name, description });
      toast('Conciliação criada com sucesso');
    }
    closeModal('reconFormModal');
    await loadRecon();
  } catch (err) {
    if (err.error) {
      const el = document.getElementById('errReconName');
      el.textContent = err.error;
      el.style.display = 'block';
    } else {
      toast('Erro ao salvar conciliação');
    }
  }
}

function clearReconErrors() {
  const el = document.getElementById('errReconName');
  el.style.display = 'none';
  el.textContent = 'Nome é obrigatório';
}

function triggerImport() {
  if (!state.loggedIn) { openModal('loginModal'); toast('Faça login para continuar'); return; }
  document.getElementById('importFileInput').value = '';
  document.getElementById('importFileInput').click();
}

async function handleImportFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  let data;
  try {
    data = JSON.parse(await file.text());
  } catch {
    toast('Arquivo JSON inválido');
    return;
  }
  try {
    await apiFetch('POST', '/api/recon/import', data);
    toast('Conciliação importada com sucesso');
    await loadRecon();
  } catch (err) {
    toast(err.error || 'Erro ao importar conciliação');
  }
}

async function duplicateRecon(id) {
  try {
    await apiFetch('POST', `/api/recon/${id}/duplicate`);
    toast('Conciliação duplicada com sucesso');
    await loadRecon();
  } catch {
    toast('Erro ao duplicar conciliação');
  }
}

let _exportData = null;

async function exportRecon(id) {
  try {
    _exportData = await apiFetch('GET', `/api/recon/${id}/export`);
    document.getElementById('exportTitle').textContent = `Exportar — ${_exportData.name}`;
    document.getElementById('exportContent').textContent = JSON.stringify(_exportData, null, 2);
    openModal('exportModal');
  } catch {
    toast('Erro ao exportar conciliação');
  }
}

function downloadExport() {
  if (!_exportData) return;
  const json = JSON.stringify(_exportData, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${_exportData.name.replace(/\s+/g, '_')}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

async function copyExport() {
  if (!_exportData) return;
  const json = JSON.stringify(_exportData, null, 2);
  try {
    await navigator.clipboard.writeText(json);
    toast('JSON copiado para a área de transferência');
  } catch {
    toast('Erro ao copiar JSON');
  }
}

// ── AUTH ──
async function doLogin() {
  const username = document.getElementById('loginUsername').value.trim();
  const senha = document.getElementById('loginSenha').value;
  const err = document.getElementById('loginError');
  err.style.display = 'none';

  if (!username || !senha) {
    err.textContent = 'Usuário e senha são obrigatórios';
    err.style.display = 'flex';
    return;
  }

  try {
    const user = await apiFetch('POST', '/api/auth/login', { username, password: senha });
    applyLogin(user);
    window.location.href = '/';
  } catch (e) {
    err.textContent = e.error || 'Erro ao autenticar';
    err.style.display = 'flex';
  }
}

function openLogoutConfirm() {
  openModal('logoutModal');
}

async function doLogout() {
  try { await apiFetch('POST', '/api/auth/logout'); } catch { /* ignora */ }
  window.location.href = '/';
}

function applyLogin(user) {
  state.loggedIn = true;
  state.user = user;
  document.getElementById('btnLogin').style.display = 'none';
  document.getElementById('userBadge').style.display = 'flex';
  document.getElementById('userAvatarNav').textContent = getInitials(user.name);
  document.getElementById('userNameNav').textContent = user.name;
  loadMenu();
}

function applyLogout() {
  state.loggedIn = false;
  state.user = null;
  document.getElementById('btnLogin').style.display = '';
  document.getElementById('userBadge').style.display = 'none';
  const navItems = document.getElementById('navItems');
  if (navItems) navItems.innerHTML = '';
}

async function loadMenu() {
  try {
    const items = await apiFetch('GET', '/api/auth/menu');
    renderMenu(items);
  } catch { /* sem menu se não autenticado */ }
}

function renderMenu(items) {
  const navItems = document.getElementById('navItems');
  if (!navItems) return;
  const path = location.pathname;
  const topLevel = items.filter(i => !i.id_parent || i.id_parent === 0);
  const byParent = {};
  items.filter(i => i.id_parent && i.id_parent !== 0).forEach(i => {
    (byParent[i.id_parent] = byParent[i.id_parent] || []).push(i);
  });
  navItems.innerHTML = topLevel.map(item => {
    const subs = byParent[item.id] || [];
    if (subs.length === 0) {
      return `<a class="nav-link${path === item.link ? ' active' : ''}" href="${item.link || '#'}">${esc(item.name)}</a>`;
    }
    const isActive = subs.some(s => path === s.link);
    return `<div class="nav-dropdown">
      <button class="nav-link${isActive ? ' active' : ''}">
        ${esc(item.name)}
        <svg class="nav-chevron" width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2 4.5L6 8.5L10 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <div class="nav-dropdown-menu">
        ${subs.map((s, idx) => `
          ${idx > 0 ? '<div class="nav-dropdown-sep"></div>' : ''}
          <a class="nav-dropdown-item${path === s.link ? ' active' : ''}" href="${s.link || '#'}">
            <div><div style="font-weight:500">${esc(s.name)}</div></div>
          </a>`).join('')}
      </div>
    </div>`;
  }).join('');
}

function getInitials(name) {
  const parts = name.trim().split(/\s+/);
  return parts.length === 1
    ? parts[0].slice(0, 2).toUpperCase()
    : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

async function checkSession() {
  try {
    const user = await apiFetch('GET', '/api/auth/me');
    applyLogin(user);
  } catch { /* sessão inativa — mantém estado deslogado */ }
}

// ── RULE FIELD ──
let rfCache = [];
let rfOptions = { rules: [], fields: [], rule_types: [], operators: [], aggregations: [] };
const rfState = { pageNum: 1, colRecon: '', colRule: '', colType: '', colField1: '', colField2: '', colAggregation: '', colOperator: '', colTolerance: '', selectedId: null };

function selectRfRow(id) {
  rfState.selectedId = id;
  updateRfFooterButtons();
}

function updateRfFooterButtons() {
  const hasSelection = rfState.selectedId != null;
  ['btnRfEdit', 'btnRfDuplicate', 'btnRfDelete'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerRfEdit() {
  if (rfState.selectedId != null) openRfForm(rfState.selectedId);
}

function footerRfDuplicate() {
  if (rfState.selectedId != null) openDuplicate('rf', rfState.selectedId);
}

function footerRfDelete() {
  if (rfState.selectedId != null) openDelete('rf', rfState.selectedId);
}

async function loadRuleField() {
  try {
    [rfCache, rfOptions] = await Promise.all([
      apiFetch('GET', '/api/rule_field'),
      apiFetch('GET', '/api/rule_field/options')
    ]);
    rfState.selectedId = null;
    populateRfFilters();

    const ruleIdParam = new URLSearchParams(location.search).get('rule_id');
    if (ruleIdParam) {
      const rule = rfOptions.rules.find(r => String(r.id) === ruleIdParam);
      if (rule) {
        rfState.colRule = rule.name;
        const sel = document.getElementById('filter-rf-rule');
        if (sel) sel.value = rule.name;
      }
    }

    renderRuleField();
  } catch {
    toast('Erro ao carregar regras x campos');
  }
}

function populateRfFilters() {
  const ids = ['filter-rf-recon', 'filter-rf-rule', 'filter-rf-type', 'filter-rf-field-1', 'filter-rf-operator', 'filter-rf-field-2', 'filter-rf-aggregation'];
  if (!document.getElementById(ids[0])) return;

  const cols = [
    { id: ids[0], vals: [...new Set(rfCache.map(r => r.recon_name))],       key: 'colRecon'      },
    { id: ids[1], vals: [...new Set(rfCache.map(r => r.rule_name))],        key: 'colRule'       },
    { id: ids[2], vals: [...new Set(rfCache.map(r => r.rule_type_name))],   key: 'colType'       },
    { id: ids[3], vals: [...new Set(rfCache.map(r => r.field1_name))],      key: 'colField1'     },
    { id: ids[4], vals: [...new Set(rfCache.map(r => r.operator_name))],    key: 'colOperator'   },
    { id: ids[5], vals: [...new Set(rfCache.map(r => r.field2_name))],      key: 'colField2'     },
    { id: ids[6], vals: [...new Set(rfCache.map(r => r.aggregation_name))], key: 'colAggregation'},
  ];
  cols.forEach(({ id, vals, key }) => {
    const sel = document.getElementById(id);
    sel.innerHTML = '<option value="">Todos</option>' +
      vals.sort((a, b) => a.localeCompare(b))
          .map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
    sel.value = rfState[key];
    rfState[key] = sel.value;
  });
}

function toggleRfFilters() {
  const row = document.getElementById('filter-row-rf');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterRfByColumn();
  }
}

function filterRfByColumn() {
  rfState.colRecon       = document.getElementById('filter-rf-recon').value;
  rfState.colRule        = document.getElementById('filter-rf-rule').value;
  rfState.colType        = document.getElementById('filter-rf-type').value;
  rfState.colField1      = document.getElementById('filter-rf-field-1').value;
  rfState.colOperator    = document.getElementById('filter-rf-operator').value;
  rfState.colField2      = document.getElementById('filter-rf-field-2').value;
  rfState.colAggregation = document.getElementById('filter-rf-aggregation').value;
  rfState.colTolerance   = document.getElementById('filter-rf-tolerance').value.trim();
  rfState.pageNum = 1;
  renderRuleField();
}

function getRfFiltered() {
  return rfCache.filter(r =>
    (!rfState.colRecon       || r.recon_name       === rfState.colRecon)       &&
    (!rfState.colRule        || r.rule_name        === rfState.colRule)        &&
    (!rfState.colType        || r.rule_type_name   === rfState.colType)        &&
    (!rfState.colField1      || r.field1_name      === rfState.colField1)      &&
    (!rfState.colOperator    || r.operator_name    === rfState.colOperator)    &&
    (!rfState.colField2      || r.field2_name      === rfState.colField2)      &&
    (!rfState.colAggregation || r.aggregation_name === rfState.colAggregation) &&
    (!rfState.colTolerance   || formatDecimalPlain(r.tolerance) === rfState.colTolerance)
  );
}

function renderRuleField() {
  const filtered = getRfFiltered();
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg = Math.min(rfState.pageNum, totalPages);
  rfState.pageNum = pg;

  const slice = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody = document.getElementById('tbody-rf');
  const empty = document.getElementById('empty-rf');
  const pag   = document.getElementById('pag-rf');

  if (!tbody) return;

  syncRowSelection(rfState, slice);
  updateRfFooterButtons();

  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }

  empty.style.display = 'none';
  pag.style.display = 'flex';

  tbody.innerHTML = slice.map(r => `
    <tr>
      <td style="text-align:center">
        <input type="radio" name="rfRowSelect" value="${r.id}" ${rfState.selectedId === r.id ? 'checked' : ''} onclick="selectRfRow(${r.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.id}</td>
      <td style="font-size:12.5px">${esc(r.recon_name)}</td>
      <td>${esc(r.rule_name)}</td>
      <td style="font-size:12.5px">${esc(r.rule_type_name)}</td>
      <td>${esc(r.field1_name)}</td>
      <td style="font-size:12.5px">${esc(r.operator_name)}</td>
      <td>${esc(r.field2_name)}</td>
      <td style="font-size:12.5px">${esc(r.aggregation_name)}</td>
      <td style="text-align:right; font-variant-numeric:tabular-nums">${r.tolerance != null ? formatDecimalPlain(r.tolerance) : '—'}</td>
    </tr>
  `).join('');

  const info  = document.getElementById('pag-info-rf');
  const start = (pg - 1) * PAGE_SIZE + 1;
  const end   = Math.min(pg * PAGE_SIZE, total);
  info.textContent = `${start}–${end} de ${total}`;

  const btns = document.getElementById('pag-btns-rf');
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeRfPage(-1)" ${pg===1?'disabled':''}>&#8249;</button>`;
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoRfPage(${i})">${i}</button>`;
  }
  html += `<button class="pag-btn" onclick="changeRfPage(1)" ${pg===totalPages?'disabled':''}>&#8250;</button>`;
  btns.innerHTML = html;
}

function changeRfPage(dir) {
  const total = Math.max(1, Math.ceil(getRfFiltered().length / PAGE_SIZE));
  rfState.pageNum = Math.max(1, Math.min(total, rfState.pageNum + dir));
  renderRuleField();
}

function gotoRfPage(n) {
  rfState.pageNum = n;
  renderRuleField();
}

function changeRfPageSize(value) {
  applyPageSize(value);
  rfState.pageNum = 1;
  renderRuleField();
}

function openRfForm(id) {
  if (!state.loggedIn) { openModal('loginModal'); toast('Faça login para continuar'); return; }

  state.editingSection = 'rf';
  state.editingId = id || null;

  document.getElementById('rfFormTitle').textContent = id ? 'Editar regra x campo' : 'Nova regra x campo';
  clearRfErrors();

  const selRule       = document.getElementById('rfFormRule');
  const selType       = document.getElementById('rfFormType');
  const selField1     = document.getElementById('rfFormField1');
  const selField2     = document.getElementById('rfFormField2');
  const selOperator   = document.getElementById('rfFormOperator');
  const selAggregation= document.getElementById('rfFormAggregation');

  selRule.innerHTML = '<option value="">Selecione...</option>' +
    rfOptions.rules.map(r => `<option value="${r.id}" data-recon="${r.recon_id}">${esc(r.recon_name)} / ${esc(r.name)}</option>`).join('');

  selType.innerHTML = '<option value="">Selecione...</option>' +
    rfOptions.rule_types.map(t => `<option value="${t.id}">${esc(t.name)}</option>`).join('');

  const populateFields = (selectedRuleId, selectedFieldId1, selectedFieldId2) => {
    const rule = rfOptions.rules.find(rr => String(rr.id) === String(selectedRuleId));
    const reconIdStr = rule ? String(rule.recon_id) : null;
    const allFields = rfOptions.fields || [];

    const side1Fields = allFields.filter(f => (!reconIdStr || String(f.recon_id) === reconIdStr) && Number(f.ds_side) === 1);
    const side2Fields = allFields.filter(f => (!reconIdStr || String(f.recon_id) === reconIdStr) && Number(f.ds_side) === 2);

    let options1 = side1Fields.map(f => `<option value="${f.id}">${esc(f.ds_name)} / ${esc(f.name)}</option>`).join('');
    let options2 = side2Fields.map(f => `<option value="${f.id}">${esc(f.ds_name)} / ${esc(f.name)}</option>`).join('');

    // If editing and selected field isn't in the filtered list, include it so it can be selected
    if (selectedFieldId1) {
      const found = side1Fields.some(f => String(f.id) === String(selectedFieldId1));
      if (!found) {
        const extra = allFields.find(f => String(f.id) === String(selectedFieldId1));
        if (extra) options1 = `<option value="${extra.id}">${esc(extra.ds_name)} / ${esc(extra.name)}</option>` + options1;
      }
    }
    if (selectedFieldId2) {
      const found = side2Fields.some(f => String(f.id) === String(selectedFieldId2));
      if (!found) {
        const extra = allFields.find(f => String(f.id) === String(selectedFieldId2));
        if (extra) options2 = `<option value="${extra.id}">${esc(extra.ds_name)} / ${esc(extra.name)}</option>` + options2;
      }
    }

    selField1.innerHTML = '<option value="">Selecione...</option>' + options1;
    selField2.innerHTML = '<option value="">Selecione...</option>' + options2;
    if (selectedFieldId1) selField1.value = selectedFieldId1;
    if (selectedFieldId2) selField2.value = selectedFieldId2;
  };

  selOperator.innerHTML = '<option value="">Selecione...</option>' +
    rfOptions.operators.map(o => `<option value="${o.id}">${esc(o.name)}</option>`).join('');
  selAggregation.innerHTML = '<option value="">Selecione...</option>' +
    (rfOptions.aggregations || []).map(a => `<option value="${a.id}">${esc(a.name)}</option>`).join('');

  const idGroup = document.getElementById('rfFormIdGroup');
  if (id) {
    const r = rfCache.find(r => r.id === id);
    idGroup.style.display = '';
    document.getElementById('rfFormId').value = r.id;
    selRule.value        = r.id_rule      || '';
    selType.value        = r.id_rule_type || '';
    // populate fields filtered by selected rule's recon
    populateFields(r.id_rule, r.id_field_1 || '', r.id_field_2 || '');
    selOperator.value    = r.id_operator  || '';
    selAggregation.value = r.id_aggregation || '';
    document.getElementById('rfFormTolerance').value = r.tolerance != null ? formatDecimalPlain(r.tolerance) : '';
  } else {
    idGroup.style.display = 'none';
    selRule.value        = '';
    selType.value        = '';
    populateFields('', '', '');
    selOperator.value    = '';
    selAggregation.value = '';
    document.getElementById('rfFormTolerance').value = '';
  }

  selRule.addEventListener('change', () => populateFields(selRule.value, '', ''));

  openModal('ruleFieldFormModal');
}

async function saveRuleField() {
  const id_rule        = document.getElementById('rfFormRule').value;
  const id_rule_type   = document.getElementById('rfFormType').value;
  const id_field_1     = document.getElementById('rfFormField1').value;
  const id_field_2     = document.getElementById('rfFormField2').value;
  const id_operator    = document.getElementById('rfFormOperator').value;
  const id_aggregation = document.getElementById('rfFormAggregation').value;
  const tolRaw         = document.getElementById('rfFormTolerance').value.trim();

  clearRfErrors();
  let valid = true;
  if (!id_rule)     { document.getElementById('errRfRule').style.display   = 'block'; valid = false; }
  if (!id_rule_type){ document.getElementById('errRfType').style.display   = 'block'; valid = false; }
  if (!id_field_1)  { document.getElementById('errRfField1').style.display = 'block'; valid = false; }
  if (!id_field_2)  { document.getElementById('errRfField2').style.display = 'block'; valid = false; }
  if (!id_operator) { document.getElementById('errRfOperator').style.display = 'block'; valid = false; }

  const field1Obj = rfOptions.fields.find(f => String(f.id) === id_field_1);
  const field2Obj = rfOptions.fields.find(f => String(f.id) === id_field_2);
  const hasTextField = (field1Obj && field1Obj.id_field_type === 3) || (field2Obj && field2Obj.id_field_type === 3);

  if (id_aggregation) {
    if (field1Obj && field1Obj.id_field_type === 3) {
      const el1 = document.getElementById('errRfField1');
      el1.textContent = 'Não é permitido agregar dados do tipo texto';
      el1.style.display = 'block';
      valid = false;
    }
    if (field2Obj && field2Obj.id_field_type === 3) {
      const el2 = document.getElementById('errRfField2');
      el2.textContent = 'Não é permitido agregar dados do tipo texto';
      el2.style.display = 'block';
      valid = false;
    }
  }

  const tolerance = tolRaw === '' ? 0 : parseFloat(tolRaw);
  if (isNaN(tolerance) || tolerance < 0) {
    document.getElementById('errRfTolerance').style.display = 'block';
    valid = false;
  } else if (tolerance !== 0 && hasTextField) {
    const elTol = document.getElementById('errRfTolerance');
    elTol.textContent = 'Não é permitido aplicar tolerância em texto';
    elTol.style.display = 'block';
    valid = false;
  }

  if (!valid) return;

  const body = {
    id_rule:      parseInt(id_rule),
    id_rule_type: id_rule_type ? parseInt(id_rule_type) : null,
    id_field_1:   parseInt(id_field_1),
    id_field_2:   parseInt(id_field_2),
    id_operator:  id_operator  ? parseInt(id_operator)  : null,
    id_aggregation: id_aggregation ? parseInt(id_aggregation) : null,
    tolerance
  };

  try {
    if (state.editingId) {
      await apiFetch('PUT', `/api/rule_field/${state.editingId}`, body);
      toast('Regra x campo atualizada com sucesso');
    } else {
      await apiFetch('POST', '/api/rule_field', body);
      toast('Regra x campo criada com sucesso');
    }
    closeModal('ruleFieldFormModal');
    await loadRuleField();
  } catch (err) {
    if (err.error) {
      // show error on field1 by default
      const el = document.getElementById('errRfField1') || document.getElementById('errRfField');
      el.textContent = err.error;
      el.style.display = 'block';
    } else {
      toast('Erro ao salvar regra x campo');
    }
  }
}

async function duplicateRuleField(id) {
  try {
    await apiFetch('POST', `/api/rule_field/${id}/duplicate`);
    toast('Regra x campo duplicada com sucesso');
    await loadRuleField();
  } catch {
    toast('Erro ao duplicar regra x campo');
  }
}

function clearRfErrors() {
  document.getElementById('errRfRule').style.display = 'none';
  document.getElementById('errRfType').style.display = 'none';
  const elField1 = document.getElementById('errRfField1');
  if (elField1) { elField1.style.display = 'none'; elField1.textContent = 'Campo 1 é obrigatório'; }
  const elField2 = document.getElementById('errRfField2');
  if (elField2) { elField2.style.display = 'none'; elField2.textContent = 'Campo 2 é obrigatório'; }
  document.getElementById('errRfOperator').style.display = 'none';
  const elTolerance = document.getElementById('errRfTolerance');
  elTolerance.style.display = 'none';
  elTolerance.textContent = 'Tolerância inválida (deve ser ≥ 0)';
}

// ── PROFILES ──
let profilesCache = [];
const profilesState = { pageNum: 1, colName: '', selectedId: null };

function selectProfileRow(id) {
  profilesState.selectedId = id;
  updateProfileFooterButtons();
}

function updateProfileFooterButtons() {
  const hasSelection = profilesState.selectedId != null;
  ['btnProfileEdit', 'btnProfileDuplicate', 'btnProfileDelete'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerProfileEdit() {
  if (profilesState.selectedId != null) openProfileForm(profilesState.selectedId);
}

function footerProfileDuplicate() {
  if (profilesState.selectedId != null) openDuplicate('profiles', profilesState.selectedId);
}

function footerProfileDelete() {
  if (profilesState.selectedId != null) openDelete('profiles', profilesState.selectedId);
}

async function loadProfiles() {
  try {
    profilesCache = await apiFetch('GET', '/api/profile');
    profilesState.selectedId = null;
    populateProfileFilters();
    renderProfiles();
  } catch { toast('Erro ao carregar perfis'); }
}

function populateProfileFilters() {
  const selName = document.getElementById('filter-profile-name');
  if (!selName) return;
  const optName = [...new Set(profilesCache.map(r => r.name))].sort();
  selName.innerHTML = '<option value="">Todos</option>' + optName.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
  selName.value = profilesState.colName;
}

function toggleProfileFilters() {
  const row = document.getElementById('filter-row-profiles');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterProfilesByColumn();
  }
}

function filterProfilesByColumn() {
  profilesState.colName = document.getElementById('filter-profile-name').value;
  profilesState.pageNum = 1;
  renderProfiles();
}

function getProfilesFiltered() {
  return profilesCache.filter(r =>
    (!profilesState.colName || r.name === profilesState.colName)
  );
}

function renderProfiles() {
  const filtered    = getProfilesFiltered();
  const total       = filtered.length;
  const totalPages  = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg          = Math.min(profilesState.pageNum, totalPages);
  profilesState.pageNum = pg;
  const slice       = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody       = document.getElementById('tbody-profiles');
  const empty       = document.getElementById('empty-profiles');
  const pag         = document.getElementById('pag-profiles');
  syncRowSelection(profilesState, slice);
  updateProfileFooterButtons();
  if (!tbody) return;
  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }
  empty.style.display = 'none';
  pag.style.display = 'flex';
  tbody.innerHTML = slice.map(r => `
    <tr style="cursor:pointer" onclick="navigateToProfileTransactions(${r.id})">
      <td style="text-align:center" onclick="event.stopPropagation()">
        <input type="radio" name="profileRowSelect" value="${r.id}" ${profilesState.selectedId === r.id ? 'checked' : ''} onclick="selectProfileRow(${r.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.id}</td>
      <td>${esc(r.name)}</td>
    </tr>`).join('');
  document.getElementById('pag-info-profiles').textContent = `${(pg-1)*PAGE_SIZE+1}–${Math.min(pg*PAGE_SIZE,total)} de ${total}`;
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeProfilesPage(-1)" ${pg===1?'disabled':''}>&#8249;</button>`;
  for (let i = startPage; i <= endPage; i++) html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoProfilesPage(${i})">${i}</button>`;
  html += `<button class="pag-btn" onclick="changeProfilesPage(1)" ${pg===totalPages?'disabled':''}>&#8250;</button>`;
  document.getElementById('pag-btns-profiles').innerHTML = html;
}

function changeProfilesPage(dir) {
  const total = Math.max(1, Math.ceil(getProfilesFiltered().length / PAGE_SIZE));
  profilesState.pageNum = Math.max(1, Math.min(total, profilesState.pageNum + dir));
  renderProfiles();
}

function gotoProfilesPage(n) { profilesState.pageNum = n; renderProfiles(); }

function changeProfilesPageSize(value) {
  applyPageSize(value);
  profilesState.pageNum = 1;
  renderProfiles();
}

function openProfileForm(id) {
  if (!state.loggedIn) { openModal('loginModal'); return; }
  state.editingSection = 'profiles';
  state.editingId = id || null;
  document.getElementById('profileFormTitle').textContent = id ? 'Editar perfil' : 'Novo perfil';
  clearProfileErrors();
  const idGroup = document.getElementById('profileFormIdGroup');
  if (id) {
    const r = profilesCache.find(r => r.id === id);
    idGroup.style.display = '';
    document.getElementById('profileFormId').value = r.id;
    document.getElementById('profileFormName').value = r.name;
  } else {
    idGroup.style.display = 'none';
    document.getElementById('profileFormName').value = '';
  }
  openModal('profileFormModal');
}

async function saveProfile() {
  const name = document.getElementById('profileFormName').value.trim();
  clearProfileErrors();
  if (!name) { document.getElementById('errProfileName').style.display = 'block'; return; }
  const body = { name };
  try {
    if (state.editingId) {
      await apiFetch('PUT', `/api/profile/${state.editingId}`, body);
      toast('Perfil atualizado com sucesso');
    } else {
      await apiFetch('POST', '/api/profile', body);
      toast('Perfil criado com sucesso');
    }
    closeModal('profileFormModal');
    await loadProfiles();
  } catch (err) {
    const el = document.getElementById('errProfileName');
    el.textContent = err.error || 'Erro ao salvar perfil';
    el.style.display = 'block';
  }
}

function clearProfileErrors() {
  const el = document.getElementById('errProfileName');
  el.style.display = 'none';
  el.textContent = 'Nome é obrigatório';
}

function navigateToProfileTransactions(profileId) {
  window.location.href = `/profile_transaction?profile_id=${profileId}`;
}

async function duplicateProfile(id) {
  try {
    await apiFetch('POST', `/api/profile/${id}/duplicate`);
    toast('Perfil duplicado com sucesso');
    await loadProfiles();
  } catch { toast('Erro ao duplicar perfil'); }
}

// ── TRANSACTIONS ──
let transactionsCache   = [];
let transactionsOptions = { transactions: [] };
const transactionsState = { pageNum: 1, colName: '', colLink: '', colParent: '', selectedId: null };

function selectTransactionRow(id) {
  transactionsState.selectedId = id;
  updateTransactionFooterButtons();
}

function updateTransactionFooterButtons() {
  const hasSelection = transactionsState.selectedId != null;
  ['btnTransactionEdit', 'btnTransactionDuplicate', 'btnTransactionDelete'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerTransactionEdit() {
  if (transactionsState.selectedId != null) openTransactionForm(transactionsState.selectedId);
}

function footerTransactionDuplicate() {
  if (transactionsState.selectedId != null) openDuplicate('transactions', transactionsState.selectedId);
}

function footerTransactionDelete() {
  if (transactionsState.selectedId != null) openDelete('transactions', transactionsState.selectedId);
}

async function loadTransactions() {
  try {
    [transactionsOptions, transactionsCache] = await Promise.all([
      apiFetch('GET', '/api/transaction/options'),
      apiFetch('GET', '/api/transaction')
    ]);
    transactionsState.selectedId = null;
    populateTransactionFilters();
    renderTransactions();
  } catch { toast('Erro ao carregar transações'); }
}

function populateTransactionFilters() {
  const map = {
    'filter-tx-name':    { vals: [...new Set(transactionsCache.map(r => r.name))].sort(),          key: 'colName' },
    'filter-tx-link':    { vals: [...new Set(transactionsCache.map(r => r.link))].sort(),          key: 'colLink' },
    'filter-tx-parent':  { vals: [...new Set(transactionsCache.map(r => r.parent_name || 'Raiz'))].sort(), key: 'colParent' }
  };
  for (const [selId, { vals, key }] of Object.entries(map)) {
    const sel = document.getElementById(selId);
    if (!sel) continue;
    sel.innerHTML = '<option value="">Todos</option>' + vals.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
    sel.value = transactionsState[key];
  }
}

function toggleTransactionFilters() {
  const row = document.getElementById('filter-row-transactions');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterTransactionsByColumn();
  }
}

function filterTransactionsByColumn() {
  transactionsState.colName    = document.getElementById('filter-tx-name').value;
  transactionsState.colLink    = document.getElementById('filter-tx-link').value;
  transactionsState.colParent  = document.getElementById('filter-tx-parent').value;
  transactionsState.pageNum = 1;
  renderTransactions();
}

function getTransactionsFiltered() {
  return transactionsCache.filter(r => {
    const parentLabel = r.parent_name || 'Raiz';
    return (!transactionsState.colName    || r.name === transactionsState.colName) &&
           (!transactionsState.colLink    || r.link === transactionsState.colLink) &&
           (!transactionsState.colParent  || parentLabel === transactionsState.colParent);
  });
}

function renderTransactions() {
  const filtered   = getTransactionsFiltered();
  const total      = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg         = Math.min(transactionsState.pageNum, totalPages);
  transactionsState.pageNum = pg;
  const slice      = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody      = document.getElementById('tbody-transactions');
  const empty      = document.getElementById('empty-transactions');
  const pag        = document.getElementById('pag-transactions');
  syncRowSelection(transactionsState, slice);
  updateTransactionFooterButtons();
  if (!tbody) return;
  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }
  empty.style.display = 'none';
  pag.style.display = 'flex';
  tbody.innerHTML = slice.map(r => `
    <tr>
      <td style="text-align:center">
        <input type="radio" name="transactionRowSelect" value="${r.id}" ${transactionsState.selectedId === r.id ? 'checked' : ''} onclick="selectTransactionRow(${r.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.id}</td>
      <td>${esc(r.name)}</td>
      <td>${r.parent_name ? esc(r.parent_name) : '<span style="color:var(--gray-400)">Raiz</span>'}</td>
      <td>${esc(r.link)}</td>
    </tr>`).join('');
  document.getElementById('pag-info-transactions').textContent = `${(pg-1)*PAGE_SIZE+1}–${Math.min(pg*PAGE_SIZE,total)} de ${total}`;
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeTransactionsPage(-1)" ${pg===1?'disabled':''}>&#8249;</button>`;
  for (let i = startPage; i <= endPage; i++) html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoTransactionsPage(${i})">${i}</button>`;
  html += `<button class="pag-btn" onclick="changeTransactionsPage(1)" ${pg===totalPages?'disabled':''}>&#8250;</button>`;
  document.getElementById('pag-btns-transactions').innerHTML = html;
}

function changeTransactionsPage(dir) {
  const total = Math.max(1, Math.ceil(getTransactionsFiltered().length / PAGE_SIZE));
  transactionsState.pageNum = Math.max(1, Math.min(total, transactionsState.pageNum + dir));
  renderTransactions();
}

function gotoTransactionsPage(n) { transactionsState.pageNum = n; renderTransactions(); }

function changeTransactionsPageSize(value) {
  applyPageSize(value);
  transactionsState.pageNum = 1;
  renderTransactions();
}

function openTransactionForm(id) {
  if (!state.loggedIn) { openModal('loginModal'); return; }
  state.editingSection = 'transactions';
  state.editingId = id || null;
  document.getElementById('transactionFormTitle').textContent = id ? 'Editar transação' : 'Nova transação';
  clearTransactionErrors();

  const selParent  = document.getElementById('transactionFormParent');
  const others     = id ? transactionsOptions.transactions.filter(t => t.id !== id) : transactionsOptions.transactions;
  selParent.innerHTML = '<option value="0">Raiz (sem pai)</option>' +
    others.map(t => `<option value="${t.id}">${esc(t.name)}</option>`).join('');

  const idGroup = document.getElementById('transactionFormIdGroup');
  if (id) {
    const r = transactionsCache.find(r => r.id === id);
    idGroup.style.display = '';
    document.getElementById('transactionFormId').value = r.id;
    selParent.value  = r.id_parent  || 0;
    document.getElementById('transactionFormName').value = r.name;
    document.getElementById('transactionFormLink').value = r.link;
  } else {
    idGroup.style.display = 'none';
    selParent.value  = '0';
    document.getElementById('transactionFormName').value = '';
    document.getElementById('transactionFormLink').value = '';
  }
  openModal('transactionFormModal');
}

async function saveTransaction() {
  const id_parent  = document.getElementById('transactionFormParent').value;
  const name       = document.getElementById('transactionFormName').value.trim();
  const link       = document.getElementById('transactionFormLink').value.trim();
  clearTransactionErrors();
  let valid = true;
  if (!name)       { document.getElementById('errTransactionName').style.display = 'block'; valid = false; }
  if (!valid) return;
  const body = { id_parent: parseInt(id_parent) || 0, name, link: link || null };
  try {
    if (state.editingId) {
      await apiFetch('PUT', `/api/transaction/${state.editingId}`, body);
      toast('Transação atualizada com sucesso');
    } else {
      await apiFetch('POST', '/api/transaction', body);
      toast('Transação criada com sucesso');
    }
    closeModal('transactionFormModal');
    await loadTransactions();
  } catch (err) {
    const el = document.getElementById('errTransactionName');
    el.textContent = err.error || 'Erro ao salvar transação';
    el.style.display = 'block';
  }
}

function clearTransactionErrors() {
  const el = document.getElementById('errTransactionName');
  el.style.display = 'none';
  el.textContent = 'Nome é obrigatório';
}

async function duplicateTransaction(id) {
  try {
    await apiFetch('POST', `/api/transaction/${id}/duplicate`);
    toast('Transação duplicada com sucesso');
    await loadTransactions();
  } catch { toast('Erro ao duplicar transação'); }
}

// ── PROFILE TRANSACTIONS ──
let profileTransactionsCache   = [];
let profileTransactionsOptions = { profiles: [], transactions: [] };
const profileTransactionsState = { pageNum: 1, colProfile: '', colTransaction: '', selectedId: null };

function selectProfileTransactionRow(id) {
  profileTransactionsState.selectedId = id;
  updateProfileTransactionFooterButtons();
}

function updateProfileTransactionFooterButtons() {
  const hasSelection = profileTransactionsState.selectedId != null;
  ['btnProfileTransactionDelete'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !hasSelection;
  });
}

function footerProfileTransactionDelete() {
  if (profileTransactionsState.selectedId != null) openDelete('profile_transaction', profileTransactionsState.selectedId);
}

async function loadProfileTransactions() {
  try {
    [profileTransactionsOptions, profileTransactionsCache] = await Promise.all([
      apiFetch('GET', '/api/profile_transaction/options'),
      apiFetch('GET', '/api/profile_transaction')
    ]);
    profileTransactionsState.selectedId = null;
    populateProfileTransactionFilters();
    const profileIdParam = new URLSearchParams(location.search).get('profile_id');
    if (profileIdParam) {
      const profile = profileTransactionsOptions.profiles.find(p => String(p.id) === profileIdParam);
      if (profile) {
        profileTransactionsState.colProfile = profile.name;
        const sel = document.getElementById('filter-pt-profile');
        if (sel) sel.value = profile.name;
      }
    }
    renderProfileTransactions();
  } catch { toast('Erro ao carregar associações'); }
}

function populateProfileTransactionFilters() {
  const map = {
    'filter-pt-profile':     { vals: [...new Set(profileTransactionsCache.map(r => r.profile_name))].sort(),     key: 'colProfile' },
    'filter-pt-transaction': { vals: [...new Set(profileTransactionsCache.map(r => r.transaction_name))].sort(), key: 'colTransaction' }
  };
  for (const [selId, { vals, key }] of Object.entries(map)) {
    const sel = document.getElementById(selId);
    if (!sel) continue;
    sel.innerHTML = '<option value="">Todos</option>' + vals.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
    sel.value = profileTransactionsState[key];
  }
}

function toggleProfileTransactionFilters() {
  const row = document.getElementById('filter-row-profile-transaction');
  const hiding = row.style.display !== 'none';
  row.style.display = hiding ? 'none' : '';
  if (hiding) {
    row.querySelectorAll('select, input').forEach(el => { el.value = ''; });
    filterProfileTransactionsByColumn();
  }
}

function filterProfileTransactionsByColumn() {
  profileTransactionsState.colProfile     = document.getElementById('filter-pt-profile').value;
  profileTransactionsState.colTransaction = document.getElementById('filter-pt-transaction').value;
  profileTransactionsState.pageNum = 1;
  renderProfileTransactions();
}

function getProfileTransactionsFiltered() {
  return profileTransactionsCache.filter(r =>
    (!profileTransactionsState.colProfile     || r.profile_name === profileTransactionsState.colProfile) &&
    (!profileTransactionsState.colTransaction || r.transaction_name === profileTransactionsState.colTransaction)
  );
}

function renderProfileTransactions() {
  const filtered   = getProfileTransactionsFiltered();
  const total      = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pg         = Math.min(profileTransactionsState.pageNum, totalPages);
  profileTransactionsState.pageNum = pg;
  const slice      = filtered.slice((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE);
  const tbody      = document.getElementById('tbody-profile-transaction');
  const empty      = document.getElementById('empty-profile-transaction');
  const pag        = document.getElementById('pag-profile-transaction');
  syncRowSelection(profileTransactionsState, slice);
  updateProfileTransactionFooterButtons();
  if (!tbody) return;
  if (slice.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    pag.style.display = 'none';
    return;
  }
  empty.style.display = 'none';
  pag.style.display = 'flex';
  tbody.innerHTML = slice.map(r => `
    <tr>
      <td style="text-align:center">
        <input type="radio" name="profileTransactionRowSelect" value="${r.id}" ${profileTransactionsState.selectedId === r.id ? 'checked' : ''} onclick="selectProfileTransactionRow(${r.id})">
      </td>
      <td style="color:var(--gray-400);font-size:12.5px">${r.id}</td>
      <td>${esc(r.profile_name)}</td>
      <td>${esc(r.transaction_name)}</td>
    </tr>`).join('');
  document.getElementById('pag-info-profile-transaction').textContent = `${(pg-1)*PAGE_SIZE+1}–${Math.min(pg*PAGE_SIZE,total)} de ${total}`;
  const maxButtons = 10;
  let startPage = Math.max(1, pg - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  startPage = Math.max(1, endPage - maxButtons + 1);
  let html = `<button class="pag-btn" onclick="changeProfileTransactionsPage(-1)" ${pg===1?'disabled':''}>&#8249;</button>`;
  for (let i = startPage; i <= endPage; i++) html += `<button class="pag-btn ${i===pg?'active':''}" onclick="gotoProfileTransactionsPage(${i})">${i}</button>`;
  html += `<button class="pag-btn" onclick="changeProfileTransactionsPage(1)" ${pg===totalPages?'disabled':''}>&#8250;</button>`;
  document.getElementById('pag-btns-profile-transaction').innerHTML = html;
}

function changeProfileTransactionsPage(dir) {
  const total = Math.max(1, Math.ceil(getProfileTransactionsFiltered().length / PAGE_SIZE));
  profileTransactionsState.pageNum = Math.max(1, Math.min(total, profileTransactionsState.pageNum + dir));
  renderProfileTransactions();
}

function gotoProfileTransactionsPage(n) { profileTransactionsState.pageNum = n; renderProfileTransactions(); }

function changeProfileTransactionsPageSize(value) {
  applyPageSize(value);
  profileTransactionsState.pageNum = 1;
  renderProfileTransactions();
}

// ── PROFILE TRANSACTIONS — ASSOCIAÇÃO EM MASSA ──
let profileTransactionBulkTree = { roots: [], byId: {} };

function buildTransactionTree(transactions) {
  const byId = {};
  transactions.forEach(t => { byId[t.id] = { ...t, children: [] }; });
  const roots = [];
  transactions.forEach(t => {
    if (t.id_parent && byId[t.id_parent]) {
      byId[t.id_parent].children.push(byId[t.id]);
    } else {
      roots.push(byId[t.id]);
    }
  });
  return { roots, byId };
}

function collectDescendantIds(id) {
  const node = profileTransactionBulkTree.byId[id];
  if (!node) return [];
  let ids = [];
  node.children.forEach(c => { ids.push(c.id); ids = ids.concat(collectDescendantIds(c.id)); });
  return ids;
}

function renderBulkTreeNode(node, depth) {
  const children = node.children.map(c => renderBulkTreeNode(c, depth + 1)).join('');
  return `
    <div style="margin-left:${depth * 20}px;padding:3px 0">
      <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
        <input type="checkbox" class="pt-tree-checkbox" value="${node.id}" data-parent="${node.id_parent}" onchange="onProfileTransactionBulkCheck(this)">
        <span>${esc(node.name)}</span>
        ${node.link ? `<span style="color:var(--gray-400);font-size:12px">${esc(node.link)}</span>` : ''}
      </label>
    </div>
    ${children}`;
}

function onProfileTransactionBulkCheck(cb) {
  const id = parseInt(cb.value);
  if (cb.checked) {
    let node = profileTransactionBulkTree.byId[id];
    while (node && node.id_parent) {
      const parentCb = document.querySelector(`.pt-tree-checkbox[value="${node.id_parent}"]`);
      if (parentCb) parentCb.checked = true;
      node = profileTransactionBulkTree.byId[node.id_parent];
    }
    collectDescendantIds(id).forEach(did => {
      const dCb = document.querySelector(`.pt-tree-checkbox[value="${did}"]`);
      if (dCb) dCb.checked = true;
    });
  } else {
    collectDescendantIds(id).forEach(did => {
      const dCb = document.querySelector(`.pt-tree-checkbox[value="${did}"]`);
      if (dCb) dCb.checked = false;
    });
  }
}

function renderProfileTransactionBulkTree() {
  const container = document.getElementById('profileTransactionBulkTree');
  const idProfile = document.getElementById('profileTransactionBulkProfile').value;
  profileTransactionBulkTree = buildTransactionTree(profileTransactionsOptions.transactions);
  container.innerHTML = profileTransactionBulkTree.roots.map(r => renderBulkTreeNode(r, 0)).join('');
  if (idProfile) {
    const checkedIds = new Set(
      profileTransactionsCache.filter(r => r.id_profile === parseInt(idProfile)).map(r => r.id_transaction)
    );
    checkedIds.forEach(id => {
      const cb = document.querySelector(`.pt-tree-checkbox[value="${id}"]`);
      if (cb) cb.checked = true;
    });
  }
}

function onProfileTransactionBulkProfileChange() {
  renderProfileTransactionBulkTree();
}

function openProfileTransactionBulkForm() {
  if (!state.loggedIn) { openModal('loginModal'); return; }
  const sel = document.getElementById('profileTransactionBulkProfile');
  sel.innerHTML = '<option value="">Selecione...</option>' +
    profileTransactionsOptions.profiles.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
  sel.value = '';
  document.getElementById('errProfileTransactionBulkProfile').style.display = 'none';
  renderProfileTransactionBulkTree();
  openModal('profileTransactionBulkModal');
}

async function saveProfileTransactionBulk() {
  const errEl = document.getElementById('errProfileTransactionBulkProfile');
  errEl.style.display = 'none';
  const idProfile = document.getElementById('profileTransactionBulkProfile').value;
  if (!idProfile) { errEl.style.display = 'block'; return; }
  const transaction_ids = [...document.querySelectorAll('.pt-tree-checkbox:checked')].map(cb => parseInt(cb.value));
  try {
    await apiFetch('PUT', '/api/profile_transaction/sync', { id_profile: parseInt(idProfile), transaction_ids });
    toast('Associações salvas com sucesso');
    closeModal('profileTransactionBulkModal');
    await loadProfileTransactions();
  } catch (err) {
    errEl.textContent = err.error || 'Erro ao salvar associações';
    errEl.style.display = 'block';
  }
}

// ── MODALS ──
function openModal(id) {
  document.getElementById(id).classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  document.body.style.overflow = '';
}

const _noClickOutside = new Set(['loginModal', 'logoutModal', 'reconFormModal', 'userFormModal', 'dsFormModal', 'fieldFormModal', 'ruleFormModal', 'ruleFieldFormModal', 'profileFormModal', 'transactionFormModal', 'profileTransactionBulkModal', 'exportModal']);
document.querySelectorAll('.modal-overlay').forEach(o => {
  if (_noClickOutside.has(o.id)) return;
  o.addEventListener('click', e => { if (e.target === o) closeModal(o.id); });
});

// ── TOAST ──
let toastTimer;
function toast(msg) {
  const el = document.getElementById('toast');
  el.innerHTML = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#4ade80" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg> ${msg}`;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}

// ── UTILS ──
function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

// Evita notação científica (ex: 1e-8) ao exibir números decimais pequenos
function formatDecimalPlain(value) {
  if (value === null || value === undefined || value === '') return '';
  const num = typeof value === 'number' ? value : parseFloat(value);
  if (isNaN(num)) return String(value);
  if (!isFinite(num)) return String(num);
  let s = num.toFixed(10);
  if (s.indexOf('.') !== -1) {
    s = s.replace(/0+$/, '').replace(/\.$/, '');
  }
  return s;
}

// ── PAGE SIZE (sincroniza os seletores já presentes no HTML da página) ──
document.querySelectorAll('.page-size-select').forEach(sel => { sel.value = String(PAGE_SIZE); });
