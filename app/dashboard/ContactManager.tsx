"use client";
import React, { useState, useEffect, useCallback } from "react";
import Toast from "../components/Toast";

export default function ContactManager() {
  type ContactRow = {
    id?: string;
    name?: string;
    role?: string;
    email?: string;
    linkedin?: string;
    phone?: string;
    leadSource?: string;
    company?: string;
    city?: string;
    industry?: string;
    sheet?: string;
  };
  const [excelSheets, setExcelSheets] = useState<{ [sheet: string]: ContactRow[] }>({});
  const [rawParsedRows, setRawParsedRows] = useState<Record<string, any[]>>({});
  const [detectedHeaders, setDetectedHeaders] = useState<string[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [previewRows, setPreviewRows] = useState<ContactRow[]>([]);
  const [contacts, setContacts] = useState<ContactRow[]>([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [error, setError] = useState("");
  const [whatsappInviteStatus, setWhatsappInviteStatus] = useState<{ contactId: string; message: string } | null>(null);
  const [sendingWhatsAppInvite, setSendingWhatsAppInvite] = useState<string | null>(null);
  const [columnMap, setColumnMap] = useState<{ [dbField: string]: string }>({});
  const [updateExisting, setUpdateExisting] = useState(false);
  const [importSelection, setImportSelection] = useState<{ [idx: number]: boolean }>({});
  const [existingEmails, setExistingEmails] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<React.ReactNode | null>(null);
  const [importResults, setImportResults] = useState<any[] | null>(null);
  const [importing, setImporting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<ContactRow>>({});
  const [showInlineAdd, setShowInlineAdd] = useState(false);
  const [inlineAddForm, setInlineAddForm] = useState<Partial<ContactRow>>({});
  
  // Search and pagination states
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(0);
  const [totalContacts, setTotalContacts] = useState(0);
  const [loadingContacts, setLoadingContacts] = useState(false);
  const pageSize = 50; // Contacts per page
  
  // Enhanced deletion filter states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteFilters, setDeleteFilters] = useState({
    industries: [] as string[],
    companies: [] as string[],
    cities: [] as string[],
    emailDomains: [] as string[],
    sources: [] as string[],
    hasPhone: null as boolean | null,
    hasLinkedIn: null as boolean | null,
    dateRange: { from: '', to: '' },
    searchText: ''
  });
  const [deletePreview, setDeletePreview] = useState<{
    contacts: ContactRow[],
    count: number,
    breakdown: Record<string, number>
  } | null>(null);
  const [deletingBulk, setDeletingBulk] = useState(false);
  const [cleanupOrphanedCompanies, setCleanupOrphanedCompanies] = useState(false);
  const [availableFilters, setAvailableFilters] = useState<{
    industries: string[],
    companies: string[],
    cities: string[],
    emailDomains: string[],
    sources: string[]
  }>({ industries: [], companies: [], cities: [], emailDomains: [], sources: [] });

  const dbFields = [
    { key: 'name', label: 'Name' },
    { key: 'role', label: 'Role' },
    { key: 'email', label: 'Email' },
    { key: 'linkedin', label: 'LinkedIn' },
    { key: 'phone', label: 'Phone' },
    { key: 'leadSource', label: 'Lead Source' },
    { key: 'company', label: 'Company' },
    { key: 'city', label: 'City' },
    { key: 'industry', label: 'Industry' }
  ];

  function handleColumnMapChange(dbField: string, sheetCol: string) {
    setColumnMap(prev => {
      const newMap = { ...prev, [dbField]: sheetCol };
      
      // Refresh preview with new mapping
      setTimeout(() => {
        refreshPreviewWithMapping(newMap);
      }, 0);
      
      return newMap;
    });
  }

  function refreshPreviewWithMapping(mapOverride?: Record<string, string>) {
    const mapToUse = mapOverride || columnMap;
    
    if (selectedSheet && rawParsedRows[selectedSheet]) {
      const rawRows = rawParsedRows[selectedSheet];
      const mappedRows = rawRows.map(r => normalize(r, selectedSheet, mapToUse));
      
      setExcelSheets(prev => ({ ...prev, [selectedSheet]: mappedRows }));
      setPreviewRows(mappedRows);
    }
  }

  // normalize a raw row to ContactRow using an optional columnMap override
  function normalize(row: Record<string, unknown>, sheetName?: string, mapOverride?: { [dbField: string]: string }): ContactRow {
    const mapToUse = mapOverride && Object.keys(mapOverride).length ? mapOverride : columnMap;
    const get = (k?: string) => {
      if (!k) return "";
      const mappedKey = (mapToUse as any)[k];
      // primary: mapped column name
      if (mappedKey && row[mappedKey] !== undefined) return String(row[mappedKey] ?? "");
      // secondary: direct key
      if (row[k] !== undefined) return String(row[k] ?? "");
      // fallback: try case-insensitive match against raw keys
      const lower = k.toLowerCase();
      for (const key of Object.keys(row)) {
        if (key.toLowerCase() === lower) return String(row[key] as any);
        if (key.toLowerCase().includes(lower)) return String(row[key] as any);
      }
      
      // Special handling for leadSource field - try more variations
      if (k === 'leadSource') {
        const sourceVariations = ['source', 'leadsource', 'lead_source', 'lead source', 'origin', 'sourcename', 'source_name'];
        
        for (const variation of sourceVariations) {
          for (const key of Object.keys(row)) {
            const keyNormalized = key.replace(/[^a-z0-9]/gi, '').toLowerCase();
            const variationNormalized = variation.replace(/[^a-z0-9]/gi, '').toLowerCase();
            if (keyNormalized === variationNormalized || keyNormalized.includes(variationNormalized)) {
              const value = String(row[key] ?? "");
              if (value.trim()) return value;
            }
          }
        }
      }
      
      // Special handling for LinkedIn field - try more variations
      if (k === 'linkedin') {
        const linkedinVariations = ['linkedin', 'linkedinurl', 'linkedin_url', 'linkedinprofile', 'linkedin_profile', 
                                   'liprofileurl', 'li_profile_url', 'contactliprofileurl', 'contact_li_profile_url', 
                                   'profileurl', 'profile_url', 'contact li profile url'];
        
        for (const variation of linkedinVariations) {
          for (const key of Object.keys(row)) {
            const keyNormalized = key.replace(/[^a-z0-9]/gi, '').toLowerCase();
            const variationNormalized = variation.replace(/[^a-z0-9]/gi, '').toLowerCase();
            if (keyNormalized === variationNormalized || keyNormalized.includes(variationNormalized)) {
              const value = String(row[key] ?? "");
              if (value.trim()) return value;
            }
          }
        }
      }
      
      return "";
    };
    
    // Get leadSource with fallback to sheet name or filename
    const leadSourceValue = get('leadSource');
    const fallbackSource = sheetName || "Unknown";
    
    return {
      name: get('name'),
      role: get('role'),
      email: get('email'),
      linkedin: get('linkedin'),
      phone: get('phone'),
      leadSource: leadSourceValue || fallbackSource, // Use sheet name as fallback if no leadSource found
      company: get('company'),
      city: get('city'),
      industry: get('industry')?.toLowerCase().trim() || get('industry'), // Normalize industry to lowercase
      sheet: sheetName || ""
    };
  }

  async function handleImportFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const isCSV = file.name.endsWith('.csv');
    const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');
  // contactsToAdd was unused — removed to satisfy lint
    if (isCSV) {
      const text = await file.text();
      const lines = text.split(/\r?\n/).filter(Boolean);
      const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim());
      const parsedRows: Record<string, any>[] = [];
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(x => x.replace(/"/g, '').trim());
        const row: Record<string, unknown> = {};
        headers.forEach((h, idx) => row[h] = values[idx]);
        parsedRows.push(row as Record<string, any>);
      }
      
      // Use filename without extension as the sheet name for CSV files
      const csvSheetName = file.name.replace(/\.(csv|CSV)$/, '') || "CSV";
      
  // Save raw parsed rows (per-sheet) and detected headers
      setRawParsedRows({ [csvSheetName]: parsedRows });
      setDetectedHeaders(headers);
      // Try to auto-map headers to DB fields if the mapping is empty.
      // Apply mapping synchronously to the preview by passing mapOverride to normalize.
      if (Object.keys(columnMap).length === 0) {
        const auto: Record<string, string> = {}; 
        autoMapHeaders(headers, auto);
        setColumnMap(auto);
        const mapped = parsedRows.map(r => normalize(r, csvSheetName, auto));
        setExcelSheets({ [csvSheetName]: mapped });
        setSelectedSheet(csvSheetName);
        setPreviewRows(mapped);
      } else {
        const rows = parsedRows.map(r => normalize(r, csvSheetName, columnMap));
        setExcelSheets({ [csvSheetName]: rows });
        setSelectedSheet(csvSheetName);
        setPreviewRows(rows);
      }
      e.target.value = '';
      return;
    } else if (isExcel) {
      try {
        const XLSX = await import('xlsx');
        const data = await file.arrayBuffer();
        const workbook = XLSX.read(data, { type: 'array' });
        const sheets: { [sheet: string]: ContactRow[] } = {};
        const rawSheets: Record<string, any[]> = {};
        for (const sheetName of workbook.SheetNames) {
          const sheet = workbook.Sheets[sheetName];
          const rows = XLSX.utils.sheet_to_json(sheet) as Record<string, unknown>[];
          rawSheets[sheetName] = rows as Record<string, any>[];
        }
        // Use first sheet headers to auto-map if needed
        const firstRaw = rawSheets[workbook.SheetNames[0]] || [];
        setRawParsedRows(rawSheets);
        if (firstRaw.length > 0) {
          const headers = Object.keys(firstRaw[0]);
          setDetectedHeaders(headers);
          if (Object.keys(columnMap).length === 0) {
            const auto: Record<string, string> = {};
            autoMapHeaders(headers, auto);
            setColumnMap(auto);
            // apply auto mapping synchronously to all sheets
            for (const sheetName of workbook.SheetNames) {
              const mapped = (rawSheets[sheetName] || []).map(r => normalize(r, sheetName, auto));
              (sheets as any)[sheetName] = mapped;
            }
          } else {
            for (const sheetName of workbook.SheetNames) {
              const mapped = (rawSheets[sheetName] || []).map(r => normalize(r, sheetName, columnMap));
              (sheets as any)[sheetName] = mapped;
            }
          }
        }
        setExcelSheets(sheets);
        setSelectedSheet(workbook.SheetNames[0]);
        setPreviewRows((sheets as any)[workbook.SheetNames[0]] || []);
        e.target.value = '';
        return;
      } catch {
        setError('Excel import failed.');
        return;
      }
    } else {
      setError('Unsupported file type.');
      return;
    }
  }

  // Try to auto-map headers from parsed CSV/xlsx to db fields
  function autoMapHeaders(headers: string[], out: Record<string,string>) {
    const norm = (s: string) => s.replace(/[^a-z0-9]/gi, '').toLowerCase();
    const headerNorms = headers.map(h => ({ raw: h, n: norm(h) }));
    
    // Enhanced mapping rules for common field variations
    const mappingRules = {
      name: ['name', 'fullname', 'contactname', 'firstname', 'first_name', 'full_name', 'contact_name'],
      role: ['role', 'title', 'position', 'jobtitle', 'job_title', 'designation'],
      email: ['email', 'emailaddress', 'email_address', 'mail'],
      linkedin: ['linkedin', 'linkedinurl', 'linkedin_url', 'linkedinprofile', 'linkedin_profile', 'liprofileurl', 'li_profile_url', 'contactliprofileurl', 'contact_li_profile_url', 'profileurl', 'profile_url'],
      phone: ['phone', 'phonenumber', 'phone_number', 'mobile', 'mobilenumber', 'mobile_number', 'contact'],
      leadSource: ['source', 'leadsource', 'lead_source', 'lead source', 'origin', 'sourcename', 'source_name'],
      company: ['company', 'companyname', 'company_name', 'organization', 'org'],
      city: ['city', 'location', 'place', 'address'],
      industry: ['industry', 'sector', 'vertical', 'businesstype', 'business_type']
    };
    
    for (const field of dbFields) {
      const fieldRules = mappingRules[field.key as keyof typeof mappingRules] || [field.key];
      
      // Try exact matches first
      for (const rule of fieldRules) {
        const candidates = headerNorms.filter(h => h.n === norm(rule));
        if (candidates.length) {
          out[field.key] = candidates[0].raw;
          break;
        }
      }
      
      // If no exact match, try contains
      if (!out[field.key]) {
        for (const rule of fieldRules) {
          const contains = headerNorms.find(h => h.n.includes(norm(rule)) || norm(rule).includes(h.n));
          if (contains) {
            out[field.key] = contains.raw;
            break;
          }
        }
      }
    }
  }

  function handleSheetSelect(sheet: string) {
    setSelectedSheet(sheet);
    setPreviewRows(excelSheets[sheet] || []);
  }

  function getPreviewValue(previewRow: ContactRow, rawRow: Record<string, any> | undefined, fieldKey: string) {
    const v = (previewRow as any)[fieldKey];
    if (v) return v;
    const mapped = columnMap[fieldKey];
    if (mapped && rawRow && rawRow[mapped] !== undefined) return String(rawRow[mapped] ?? '');
    if (rawRow) {
      const lower = fieldKey.toLowerCase();
      for (const k of Object.keys(rawRow)) {
        if (k.toLowerCase().includes(lower)) return String(rawRow[k] ?? '');
      }
    }
    return '';
  }

  async function handleImportPreviewed() {
    if (!previewRows.length) return;
    // Build a list of rows to import and avoid duplicates client-side
    // Use rawParsedRows where possible so we submit original fields
    const toImportRaw: Record<string, any>[] = [];
    // helper: map a raw row to DB keys using columnMap or header heuristics
    function mapToDbKeys(rawRow: Record<string, any>, previewRow: ContactRow) {
      const out: Record<string, any> = {};
      // prefer explicit columnMap
      for (const f of dbFields) {
        const mappedCol = columnMap[f.key];
        if (mappedCol && rawRow && rawRow[mappedCol] !== undefined) {
          out[f.key] = rawRow[mappedCol];
          continue;
        }
        // fallback: previewRow already has normalized value
        if ((previewRow as any)[f.key]) {
          out[f.key] = (previewRow as any)[f.key];
          continue;
        }
        // final fallback: try to find a header that contains the field key
        if (rawRow) {
          // Special enhanced handling for LinkedIn field
          if (f.key === 'linkedin') {
            const linkedinVariations = ['linkedin', 'linkedinurl', 'linkedin_url', 'linkedinprofile', 'linkedin_profile', 
                                       'liprofileurl', 'li_profile_url', 'contactliprofileurl', 'contact_li_profile_url', 
                                       'profileurl', 'profile_url', 'contact li profile url'];
            
            for (const variation of linkedinVariations) {
              for (const k of Object.keys(rawRow)) {
                const keyNormalized = k.replace(/[^a-z0-9]/gi, '').toLowerCase();
                const variationNormalized = variation.replace(/[^a-z0-9]/gi, '').toLowerCase();
                if (keyNormalized === variationNormalized || keyNormalized.includes(variationNormalized)) {
                  const value = String(rawRow[k] ?? "");
                  if (value.trim()) {
                    out[f.key] = value;
                    break;
                  }
                }
              }
              if (out[f.key]) break;
            }
          } else {
            // Regular field matching for non-LinkedIn fields
            const lowKey = f.key.toLowerCase();
            for (const k of Object.keys(rawRow)) {
              if (k.toLowerCase().includes(lowKey)) {
                out[f.key] = rawRow[k];
                break;
              }
            }
          }
        }
      }
      // also include raw fields commonly used by server (domain, company_name)
      if (rawRow) {
        if (!out.domain && rawRow.domain) out.domain = rawRow.domain;
        if (!out.company_name && rawRow.company_name) out.company_name = rawRow.company_name;
      }
      // preserve sheet
      out.sheet = selectedSheet || previewRow.sheet || out.sheet;
      return out;
    }

    for (let i = 0; i < previewRows.length; i++) {
      if (importSelection[i] === false) continue;
      const raw = (rawParsedRows as any)[selectedSheet]?.[i] || previewRows[i];
      // avoid importing duplicates by email using previewRows normalized email
      const candidateEmail = (previewRows[i].email || raw?.email || raw?.Email || raw?.EMAIL || '').toString();
      if (candidateEmail && existingEmails.has(candidateEmail)) continue;
      const mapped = mapToDbKeys(raw || {}, previewRows[i]);
      toImportRaw.push(mapped);
    }
    const toImport = toImportRaw;
    if (toImport.length === 0) {
      setToast('No new contacts to import');
      return;
    }
    try {
      setImporting(true);
      // Send both preview and commit so server can accept a single-call import
      const res = await fetch('/api/contacts/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contacts: toImport, preview: true, commit: true, updateExisting }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data?.error || 'Bulk import failed');
        setToast('Bulk import failed');
        // server may return report or errors
        setImportResults(data?.report || data?.errors || data?.details || null);
      } else {
        setToast('Imported contacts successfully');
        setImportResults(data?.report || data?.data || []);
      }
    } catch {
      setError('Bulk import failed');
      setToast('Bulk import failed');
    }
    finally {
      setImporting(false);
    }
    fetchContacts();
    setError('');
    setExcelSheets({});
    setPreviewRows([]);
    setSelectedSheet("");
    setImportSelection({});
  setToast('Imported contacts successfully');
  }

  const fetchContacts = useCallback(() => {
    setLoadingContacts(true);
    
    const url = new URL("/api/contacts", window.location.origin);
    url.searchParams.set("limit", String(pageSize));
    url.searchParams.set("offset", String(currentPage * pageSize));
    if (searchQuery.trim()) {
      url.searchParams.set("q", searchQuery.trim());
    }
    
    fetch(url.toString())
      .then((res) => res.json())
      .then((data) => {
        setContacts(data.contacts || []);
        setTotalContacts(data.total || 0);
        setLoadingContacts(false);
      }).catch(() => {
        setLoadingContacts(false);
      });
  }, [searchQuery, currentPage, pageSize]);

  function exportCSV() {
    if (!contacts.length) return;
    const header = ["Name", "Role", "Email", "LinkedIn", "Phone", "LeadSource", "Company"];
    const rows = contacts.map(c => [
      c.name || "",
      c.role || "",
      c.email || "",
      c.linkedin || "",
      c.phone || "",
      c.leadSource || "",
      c.company || ""
    ]);
    const csvContent = [header, ...rows].map(r => r.map(x => `"${x}"`).join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "contacts.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  useEffect(() => {
    setExistingEmails(new Set(contacts.map(c => c.email || "")));
  }, [contacts]);

  async function handleAddContact(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!name || !email || !company) {
      setError("All fields are required.");
      return;
    }
    const res = await fetch("/api/contacts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, company }),
    });
    if (res.ok) {
      setName("");
      setEmail("");
      setCompany("");
      fetchContacts();
  setToast('Contact added');
    } else {
      setError("Failed to add contact.");
  setToast('Failed to add contact');
    }
  }

  function startEdit(c: ContactRow) {
    setEditingId(c.id || null);
    setEditForm({ ...c });
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm({});
  }

  async function saveEdit(id?: string) {
    if (!id) return;
    try {
      const patchBody: any = {};
      // copy only fields that exist in editForm
      ['name','role','email','linkedin','phone','leadSource','company','city','industry'].forEach((k) => {
        if ((editForm as any)[k] !== undefined) patchBody[k] = (editForm as any)[k];
      });
      const res = await fetch(`/api/contacts/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patchBody),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setToast(data?.error || 'Failed to update contact');
      } else {
        setToast('Contact updated');
      }
    } catch {
      setToast('Failed to update contact');
    }
    cancelEdit();
    fetchContacts();
  }

  async function sendWhatsAppInviteToContact(contact: any) {
    if (!contact.phone) {
      setWhatsappInviteStatus({ contactId: contact.id, message: '❌ No phone number available for this contact' });
      setTimeout(() => setWhatsappInviteStatus(null), 5000);
      return;
    }

    setSendingWhatsAppInvite(contact.id);
    setWhatsappInviteStatus(null);

    try {
      // Auto-detect demo URL
      let demoUrl = '';
      try {
        const ngrokRes = await fetch('http://localhost:4040/api/tunnels', { 
          signal: AbortSignal.timeout(2000) 
        }).catch(() => null);
        
        if (ngrokRes?.ok) {
          const data = await ngrokRes.json();
          const tunnels = data.tunnels || [];
          const httpsTunnel = tunnels.find((t: any) => t.proto === 'https');
          if (httpsTunnel?.public_url) {
            demoUrl = httpsTunnel.public_url;
          }
        }
      } catch {}

      if (!demoUrl) {
        demoUrl = process.env.NEXT_PUBLIC_APP_URL || window.location.origin;
      }

      const response = await fetch('/api/demo/whatsapp-invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: contact.phone,
          name: contact.name || contact.email,
          demoUrl: demoUrl
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setWhatsappInviteStatus({ 
          contactId: contact.id, 
          message: `✅ WhatsApp invite sent to ${contact.name || contact.email}` 
        });
        setTimeout(() => setWhatsappInviteStatus(null), 5000);
      } else {
        throw new Error(data.error || 'Failed to send WhatsApp invitation');
      }
    } catch (error: any) {
      setWhatsappInviteStatus({ 
        contactId: contact.id, 
        message: `❌ Error: ${error.message}` 
      });
      setTimeout(() => setWhatsappInviteStatus(null), 5000);
    } finally {
      setSendingWhatsAppInvite(null);
    }
  }

  async function deleteContact(id?: string) {
    if (!id) return;
    if (!confirm('Delete this contact?')) return;
    try {
      const res = await fetch(`/api/contacts/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setToast(data?.error || 'Failed to delete contact');
      } else {
        setToast('Contact deleted');
      }
    } catch {
      setToast('Failed to delete contact');
    }
    fetchContacts();
  }

  // Enhanced bulk deletion functions
  async function loadFilterOptions() {
    try {
      const industries = [...new Set(contacts.map(c => c.industry ? c.industry.trim() : null).filter(Boolean))].sort() as string[];
      const companies = [...new Set(contacts.map(c => c.company).filter(Boolean))].sort() as string[];
      const cities = [...new Set(contacts.map(c => c.city).filter(Boolean))].sort() as string[];
      const emailDomains = [...new Set(
        contacts
          .map(c => c.email?.split('@')[1])
          .filter(Boolean)
      )].sort() as string[];
      const sources = [...new Set(contacts.map(c => c.leadSource).filter(Boolean))].sort() as string[];

      setAvailableFilters({ industries, companies, cities, emailDomains, sources });
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
  }

  function openDeleteModal() {
    setShowDeleteModal(true);
    loadFilterOptions();
    // Reset filters
    setDeleteFilters({
      industries: [],
      companies: [],
      cities: [],
      emailDomains: [],
      sources: [],
      hasPhone: null,
      hasLinkedIn: null,
      dateRange: { from: '', to: '' },
      searchText: ''
    });
    setDeletePreview(null);
  }

  function applyFilters(contactList: ContactRow[]) {
    return contactList.filter(contact => {
      // Industry filter
      if (deleteFilters.industries.length > 0) {
        if (!contact.industry || !deleteFilters.industries.includes(contact.industry)) {
          return false;
        }
      }

      // Company filter
      if (deleteFilters.companies.length > 0) {
        if (!contact.company || !deleteFilters.companies.includes(contact.company)) {
          return false;
        }
      }

      // City filter
      if (deleteFilters.cities.length > 0) {
        if (!contact.city || !deleteFilters.cities.includes(contact.city)) {
          return false;
        }
      }

      // Email domain filter
      if (deleteFilters.emailDomains.length > 0) {
        const domain = contact.email?.split('@')[1];
        if (!domain || !deleteFilters.emailDomains.includes(domain)) {
          return false;
        }
      }

      // Source filter
      if (deleteFilters.sources.length > 0) {
        if (!contact.leadSource || !deleteFilters.sources.includes(contact.leadSource)) {
          return false;
        }
      }

      // Phone filter
      if (deleteFilters.hasPhone !== null) {
        const hasPhone = !!(contact.phone && contact.phone.trim());
        if (deleteFilters.hasPhone !== hasPhone) {
          return false;
        }
      }

      // LinkedIn filter  
      if (deleteFilters.hasLinkedIn !== null) {
        const hasLinkedIn = !!(contact.linkedin && contact.linkedin.trim());
        if (deleteFilters.hasLinkedIn !== hasLinkedIn) {
          return false;
        }
      }

      // Search text filter
      if (deleteFilters.searchText) {
        const searchLower = deleteFilters.searchText.toLowerCase();
        const matchesSearch = 
          contact.name?.toLowerCase().includes(searchLower) ||
          contact.email?.toLowerCase().includes(searchLower) ||
          contact.company?.toLowerCase().includes(searchLower) ||
          contact.role?.toLowerCase().includes(searchLower) ||
          contact.leadSource?.toLowerCase().includes(searchLower);
        
        if (!matchesSearch) {
          return false;
        }
      }

      return true;
    });
  }

  function generateDeletePreview() {
    const filteredContacts = applyFilters(contacts);
    
    // Generate breakdown by different criteria
    const breakdown: Record<string, number> = {};
    
    // By industry
    const industryBreakdown = filteredContacts.reduce((acc, contact) => {
      const industry = contact.industry || 'No Industry';
      acc[industry] = (acc[industry] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    // By company
    const companyBreakdown = filteredContacts.reduce((acc, contact) => {
      const company = contact.company || 'No Company';
      acc[company] = (acc[company] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    breakdown['Industries'] = Object.keys(industryBreakdown).length;
    breakdown['Companies'] = Object.keys(companyBreakdown).length;
    breakdown['With Phone'] = filteredContacts.filter(c => c.phone).length;
    breakdown['With LinkedIn'] = filteredContacts.filter(c => c.linkedin).length;

    setDeletePreview({
      contacts: filteredContacts.slice(0, 10), // Show first 10 for preview
      count: filteredContacts.length,
      breakdown
    });
  }

  async function executeBulkDelete() {
    if (!deletePreview || deletePreview.count === 0) {
      setToast('No contacts to delete');
      return;
    }

    const confirmMessage = `Are you sure you want to delete ${deletePreview.count} contacts? This action cannot be undone.`;
    if (!confirm(confirmMessage)) {
      return;
    }

    setDeletingBulk(true);
    try {
      const filteredContacts = applyFilters(contacts);
      const contactIds = filteredContacts.map(c => c.id).filter(Boolean);

      // Delete in batches to avoid overwhelming the server
      const batchSize = 50;
      let deletedCount = 0;

      for (let i = 0; i < contactIds.length; i += batchSize) {
        const batch = contactIds.slice(i, i + batchSize);
        
        const deletePromises = batch.map(id => 
          fetch(`/api/contacts/${id}`, { method: 'DELETE' })
        );
        
        await Promise.all(deletePromises);
        deletedCount += batch.length;
        
        // Update progress
        setToast(`Deleted ${deletedCount}/${contactIds.length} contacts...`);
      }

      let cleanupMessage = `Successfully deleted ${deletedCount} contacts`;
      
      // Clean up orphaned companies if requested
      if (cleanupOrphanedCompanies) {
        setToast('Cleaning up orphaned companies...');
        try {
          const cleanupResponse = await fetch('/api/companies/cleanup-orphaned', { 
            method: 'POST' 
          });
          const cleanupResult = await cleanupResponse.json();
          
          if (cleanupResponse.ok && cleanupResult.deletedCount > 0) {
            cleanupMessage += ` and cleaned up ${cleanupResult.deletedCount} orphaned companies`;
          }
        } catch (cleanupError) {
          console.warn('Company cleanup failed:', cleanupError);
          cleanupMessage += ' (company cleanup failed)';
        }
      }
      
      setToast(cleanupMessage);
      setShowDeleteModal(false);
      fetchContacts(); // Refresh the contact list

    } catch (error) {
      setToast('Failed to delete contacts: ' + (error as Error).message);
    } finally {
      setDeletingBulk(false);
    }
  }

  function toggleInlineAdd() {
    setShowInlineAdd(v => !v);
    setInlineAddForm({});
  }

  async function saveInlineAdd() {
    const body: any = {
      name: inlineAddForm.name || null,
      email: inlineAddForm.email || null,
      company: inlineAddForm.company || null,
      role: inlineAddForm.role || null,
      linkedin: inlineAddForm.linkedin || null,
      phone: inlineAddForm.phone || null,
      leadSource: inlineAddForm.leadSource || null,
      city: inlineAddForm.city || null,
      industry: inlineAddForm.industry || null,
    };
    if (!body.name || !body.email) {
      setToast('Name and email required');
      return;
    }
    try {
      const res = await fetch('/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setToast(data?.error || 'Failed to add contact');
      } else {
        setToast('Contact added');
      }
    } catch {
      setToast('Failed to add contact');
    }
    setShowInlineAdd(false);
    setInlineAddForm({});
    fetchContacts();
  }

  async function exportExcel() {
    if (!contacts.length) return;
    const XLSX = await import('xlsx');
    // Group contacts by sheet
    const grouped: { [sheet: string]: Record<string, unknown>[] } = {};
    for (const c of contacts) {
      const sheet = (c.sheet as string) || 'Sheet1';
      if (!grouped[sheet]) grouped[sheet] = [];
      grouped[sheet].push({
        Name: c.name,
        Role: c.role,
        Email: c.email,
        LinkedIn: c.linkedin,
        Phone: c.phone,
        LeadSource: c.leadSource,
        Company: c.company,
        City: c.city,
        Industry: c.industry
      });
    }
    const workbook = XLSX.utils.book_new();
    for (const sheetName of Object.keys(grouped)) {
      const ws = XLSX.utils.json_to_sheet(grouped[sheetName]);
      XLSX.utils.book_append_sheet(workbook, ws, sheetName);
    }
    const wbout = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([wbout], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'contacts.xlsx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  setToast('Export started — check your downloads');
  }

  function handleImportCheckbox(idx: number, checked: boolean) {
    setImportSelection(prev => ({ ...prev, [idx]: checked }));
  }

  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded shadow w-full mb-8">
      <h2 className="text-xl font-bold mb-4">Contact Management</h2>

      <div className="mb-6">
        {!showAddForm ? (
          <div className="flex gap-2">
            <button className="bg-blue-600 text-white font-semibold px-4 py-2 rounded shadow hover:bg-blue-700" onClick={()=>setShowAddForm(true)}>Add Contact</button>
            <button className="bg-red-600 text-white font-semibold px-4 py-2 rounded shadow hover:bg-red-700" onClick={openDeleteModal}>Delete Contacts</button>
          </div>
        ) : (
          <form onSubmit={async (e)=>{ e.preventDefault(); await handleAddContact(e); setShowAddForm(false); }}>
            <div className="grid grid-cols-2 gap-2 mb-2">
              <input className="border p-2 rounded" placeholder="Name" value={name} onChange={e=>setName(e.target.value)} required />
              <input className="border p-2 rounded" placeholder="Role" value={''} onChange={()=>{}} />
              <input className="border p-2 rounded" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} required />
              <input className="border p-2 rounded" placeholder="LinkedIn" value={''} onChange={()=>{}} />
              <input className="border p-2 rounded" placeholder="Phone" value={''} onChange={()=>{}} />
              <input className="border p-2 rounded" placeholder="Lead Source" value={''} onChange={()=>{}} />
              <input className="border p-2 rounded" placeholder="Company" value={company} onChange={e=>setCompany(e.target.value)} required />
              <input className="border p-2 rounded" placeholder="City" value={''} onChange={()=>{}} />
              <input className="border p-2 rounded" placeholder="Industry" value={''} onChange={()=>{}} />
            </div>
            {error && <div className="text-red-500 mb-2">{error}</div>}
            <div className="flex gap-2">
              <button type="submit" className="bg-blue-600 text-white font-semibold px-4 py-2 rounded shadow hover:bg-blue-700">Save Contact</button>
              <button type="button" className="bg-gray-300 px-4 py-2 rounded" onClick={()=>setShowAddForm(false)}>Cancel</button>
            </div>
          </form>
        )}
      </div>
      <div className="flex gap-4 mb-4">
        <label className="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700 cursor-pointer">
          Import CSV/Excel
          <input type="file" accept=".csv,.xlsx,.xls" style={{ display: 'none' }} onChange={handleImportFile} />
        </label>
        <button className="bg-blue-500 text-white px-4 py-2 rounded shadow hover:bg-blue-600" onClick={exportCSV}>
          Export CSV
        </button>
        <button className="bg-purple-600 text-white px-4 py-2 rounded shadow hover:bg-purple-700" onClick={exportExcel}>
          Export Excel (Multi-Sheet)
        </button>
      </div>
      {/* Sheet selection and preview for import */}
  {Object.keys(excelSheets).length > 0 && (
        <div className="mb-4">
          <div className="mb-2 font-semibold">Select sheet to preview/import:</div>
          <div className="flex gap-2 mb-2">
            {Object.keys(excelSheets).map(sheet => (
              <button key={sheet} className={`px-3 py-1 rounded ${selectedSheet === sheet ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}`} onClick={() => handleSheetSelect(sheet)}>{sheet}</button>
            ))}
          </div>
          {detectedHeaders && detectedHeaders.length > 0 && (
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Detected headers: {detectedHeaders.join(', ')}</div>
          )}
          {/* Column mapping UI */}
          <div className="mb-4 p-3 border rounded bg-gray-50 dark:bg-gray-800">
            <div className="flex items-center justify-between mb-2">
              <div className="font-semibold">Map Excel/CSV columns to database fields:</div>
              <div className="flex gap-2">
                <button 
                  className="text-xs bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
                  onClick={() => {
                    const auto: Record<string, string> = {};
                    autoMapHeaders(detectedHeaders, auto);
                    setColumnMap(auto);
                    refreshPreviewWithMapping(auto);
                  }}
                >
                  Auto Map
                </button>
                <button 
                  className="text-xs bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded hover:bg-gray-300"
                  onClick={() => {
                    setColumnMap({});
                    refreshPreviewWithMapping({});
                  }}
                >
                  Clear All
                </button>
              </div>
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-3">
              <strong>Instructions:</strong> For each database field (left), select the corresponding column from your Excel/CSV file (right)
            </div>
            {/* Mapping validation status */}
            <div className="mb-3 p-2 bg-white dark:bg-gray-700 rounded border">
              <div className="text-xs font-medium mb-1">Mapping Status:</div>
              <div className="flex flex-wrap gap-2">
                {['name', 'email'].map(field => {
                  const isMapped = !!columnMap[field];
                  const fieldLabel = dbFields.find(f => f.key === field)?.label || field;
                  return (
                    <span 
                      key={field}
                      className={`text-xs px-2 py-1 rounded ${
                        isMapped 
                          ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' 
                          : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                      }`}
                    >
                      {fieldLabel}: {isMapped ? '✓' : '✗'}
                    </span>
                  );
                })}
                <span className="text-xs text-gray-500">
                  Optional: {dbFields.filter(f => !['name', 'email'].includes(f.key) && columnMap[f.key]).length} mapped
                </span>
              </div>
            </div>
            <div className="grid gap-2">
              {dbFields.map(field => (
                <div key={field.key} className="flex items-center gap-3 p-2 bg-white dark:bg-gray-700 rounded border">
                  <div className="w-28 text-right">
                    <span className="font-medium text-blue-700 dark:text-blue-300 text-sm">
                      {field.label}
                    </span>
                    <div className="text-xs text-gray-500">(Database)</div>
                  </div>
                  <div className="text-gray-400">=</div>
                  <select
                    className="flex-1 border rounded px-2 py-1 bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 text-sm"
                    value={columnMap[field.key] || ""}
                    onChange={e => handleColumnMapChange(field.key, e.target.value)}
                  >
                    <option value="">-- Select Excel/CSV column --</option>
                    {detectedHeaders.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                  {columnMap[field.key] && (
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-green-600 dark:text-green-400">✓</span>
                      <span className="text-xs text-gray-600">
                        "{columnMap[field.key]}"
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900 rounded">
              <div className="text-xs text-blue-800 dark:text-blue-200 mb-1">
                <strong>Available columns in your file:</strong>
              </div>
              <div className="text-xs text-blue-700 dark:text-blue-300">
                {detectedHeaders.join(' • ')}
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              💡 Tip: Essential fields are <strong>Name</strong> and <strong>Email</strong>. Other fields are optional.
            </div>
          </div>
          <div className="mb-2">Previewing <strong>{selectedSheet}</strong> ({previewRows.length} rows):</div>
          <div className="mb-2 flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={updateExisting} onChange={e=>setUpdateExisting(e.target.checked)} />
              <span>Update existing contacts (match by email/phone)</span>
            </label>
          </div>
          <table className="w-full text-xs border border-gray-200 dark:border-gray-700 rounded mb-2">
            <thead>
              <tr className="bg-white dark:bg-gray-800">
                <th className="p-1">Import?</th>
                <th className="p-1">Name</th>
                <th className="p-1">Role</th>
                <th className="p-1">Email</th>
                <th className="p-1">LinkedIn</th>
                <th className="p-1">Phone</th>
                <th className="p-1">Lead Source</th>
                <th className="p-1">Company</th>
                <th className="p-1">City</th>
                <th className="p-1">Industry</th>
                <th className="p-1">Sheet</th>
                <th className="p-1">Duplicate?</th>
              </tr>
            </thead>
            <tbody>
              {previewRows.map((c, idx) => {
                const isDuplicate = existingEmails.has(c.email || "");
                const raw = (rawParsedRows as any)[selectedSheet]?.[idx] || undefined;
                const nameVal = getPreviewValue(c, raw, 'name');
                const roleVal = getPreviewValue(c, raw, 'role');
                const emailVal = getPreviewValue(c, raw, 'email');
                const linkedinVal = getPreviewValue(c, raw, 'linkedin');
                const phoneVal = getPreviewValue(c, raw, 'phone');
                const leadVal = getPreviewValue(c, raw, 'leadSource');
                const companyVal = getPreviewValue(c, raw, 'company');
                const cityVal = getPreviewValue(c, raw, 'city');
                const industryVal = getPreviewValue(c, raw, 'industry');
                const sheetVal = getPreviewValue(c, raw, 'sheet') || c.sheet || '';
                return (
                  <tr key={idx} className="border-t border-gray-200 dark:border-gray-700">
                    <td className="p-1 text-center">
                      <input
                        type="checkbox"
                        checked={importSelection[idx] !== false}
                        onChange={e => handleImportCheckbox(idx, e.target.checked)}
                        disabled={isDuplicate}
                      />
                    </td>
                    <td className="p-1">{nameVal}</td>
                    <td className="p-1">{roleVal}</td>
                    <td className="p-1">{emailVal}</td>
                    <td className="p-1">{linkedinVal ? <a href={linkedinVal} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">{linkedinVal}</a> : ''}</td>
                    <td className="p-1">{phoneVal}</td>
                    <td className="p-1">{leadVal}</td>
                    <td className="p-1">{companyVal}</td>
                    <td className="p-1">{cityVal}</td>
                    <td className="p-1">{industryVal}</td>
                    <td className="p-1">{sheetVal}</td>
                    <td className="p-1 text-red-600 font-bold">{isDuplicate ? "Yes" : "No"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="flex items-center gap-3">
            <button className="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700" onClick={handleImportPreviewed} disabled={importing}>Import Previewed Contacts</button>
            {importing && (
              <div className="w-48 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden h-2">
                <div className="h-2 bg-green-500 animate-[progress_1.2s_linear_infinite]" style={{width:'40%'}} />
              </div>
            )}
          </div>
        </div>
      )}
      {importResults && (
        <div className="mt-4 p-3 border rounded bg-gray-50 dark:bg-gray-800">
          <div className="font-semibold mb-2">Import Results</div>
          <ul className="text-sm space-y-1 max-h-48 overflow-auto">
            {Array.isArray(importResults) && importResults.length === 0 && <li className="text-sm text-gray-500">No report returned.</li>}
            {importResults.map((r: any, i: number) => {
              // normalise server report fields
              const status = r.status || r.valid || r.ok || r.result || r === 'ok' ? 'ok' : r.status || 'skipped';
              const reason = r.reason || r.error || r.message || (status === 'ok' ? '' : 'Failed');
              const email = r.email || r?.contact?.email || r?.row?.email || '';
              return (
                <li key={r.index ?? i} className={`${status === 'ok' || status === 'OK' || status === 'ok' ? 'text-green-700' : 'text-red-600'}`}>
                  Row {('index' in r) ? (r.index + 1) : (i + 1)}: {email || '<no email>'} — {status === 'ok' || status === 'OK' ? 'OK' : reason}
                </li>
              );
            })}
          </ul>
        </div>
      )}
      <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
        <strong>CSV/Excel format:</strong> Name, Role, Email, LinkedIn, Phone, LeadSource, Company<br />
        Example: "John Doe", "Manager", "john@company.com", "linkedin.com/in/johndoe", "1234567890", "Web", "Company Inc"
      </div>
      
      {/* Search Bar */}
      <div className="mb-4">
        <div className="flex gap-2 items-center">
          <input
            type="text"
            placeholder="Search contacts by name, email, company, role, industry, source, phone, or city..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(0); // Reset to first page when searching
            }}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {searchQuery && (
            <button
              onClick={() => {
                setSearchQuery("");
                setCurrentPage(0);
              }}
              className="bg-gray-500 text-white px-3 py-2 rounded hover:bg-gray-600"
            >
              Clear
            </button>
          )}
        </div>
        
        {/* Search Results Info */}
        {totalContacts > 0 && (
          <div className="text-sm text-gray-600 mt-2">
            {searchQuery ? (
              <>Showing {contacts.length} of {totalContacts} contacts matching "{searchQuery}"</>
            ) : (
              <>Showing {contacts.length} of {totalContacts} total contacts</>
            )}
          </div>
        )}
      </div>
      
      <h3 className="text-lg font-bold mb-2">Contacts List</h3>
      {loadingContacts ? (
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 animate-pulse" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 animate-pulse" />
          <div className="h-36 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
        </div>
      ) : contacts.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {searchQuery ? `No contacts found matching "${searchQuery}"` : "No contacts found."}
        </div>
      ) : (
        <div className="shadow-sm">
          <table className="w-full text-sm border-collapse border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 table-fixed">
            <colgroup>
              <col className="w-[12%]" />
              <col className="w-[10%]" />
              <col className="w-[18%]" />
              <col className="w-[8%]" />
              <col className="w-[11%]" />
              <col className="w-[9%]" />
              <col className="w-[14%]" />
              <col className="w-[8%]" />
              <col className="w-[10%]" />
              <col className="w-[12%]" />
            </colgroup>
            <thead>
              <tr className="bg-gray-100 dark:bg-gray-700">
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">Name</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">Role</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">Email</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">LinkedIn</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">Phone</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">Source</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">Company</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">City</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-left text-gray-900 dark:text-gray-100 font-semibold text-xs">Industry</th>
                <th className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-center text-gray-900 dark:text-gray-100 font-semibold text-xs">Actions</th>
              </tr>
            </thead>
            <tbody>
              {showInlineAdd && (
                <tr className="bg-green-50 dark:bg-green-900/20">
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Name" value={inlineAddForm.name || ''} onChange={e=>setInlineAddForm(prev=>({...prev,name:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Role" value={inlineAddForm.role || ''} onChange={e=>setInlineAddForm(prev=>({...prev,role:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Email" value={inlineAddForm.email || ''} onChange={e=>setInlineAddForm(prev=>({...prev,email:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="LinkedIn" value={inlineAddForm.linkedin || ''} onChange={e=>setInlineAddForm(prev=>({...prev,linkedin:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Phone" value={inlineAddForm.phone || ''} onChange={e=>setInlineAddForm(prev=>({...prev,phone:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Source" value={inlineAddForm.leadSource || ''} onChange={e=>setInlineAddForm(prev=>({...prev,leadSource:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Company" value={inlineAddForm.company || ''} onChange={e=>setInlineAddForm(prev=>({...prev,company:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="City" value={inlineAddForm.city || ''} onChange={e=>setInlineAddForm(prev=>({...prev,city:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2"><input className="w-full border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Industry" value={inlineAddForm.industry || ''} onChange={e=>setInlineAddForm(prev=>({...prev,industry:e.target.value}))} /></td>
                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-center">
                    <div className="flex gap-1 justify-center">
                      <button className="bg-green-600 hover:bg-green-700 text-white px-1 py-1 rounded text-xs" onClick={saveInlineAdd}>Save</button>
                      <button className="bg-gray-500 hover:bg-gray-600 text-white px-1 py-1 rounded text-xs" onClick={toggleInlineAdd}>Cancel</button>
                    </div>
                  </td>
                </tr>
              )}

              {contacts.map((c) => (
                <React.Fragment key={c.id || c.email}>
                  {whatsappInviteStatus && whatsappInviteStatus.contactId === c.id && (
                    <tr className="bg-green-50 dark:bg-green-900/20">
                      <td colSpan={10} className="border border-gray-300 dark:border-gray-600 px-3 py-2 text-center">
                        <div className={`text-sm ${
                          whatsappInviteStatus.message.includes('✅') 
                            ? 'text-green-600 dark:text-green-400' 
                            : 'text-red-600 dark:text-red-400'
                        }`}>
                          {whatsappInviteStatus.message}
                        </div>
                      </td>
                    </tr>
                  )}
                  <tr className="hover:bg-gray-50 dark:hover:bg-gray-700 bg-white dark:bg-gray-800">
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-gray-900 dark:text-gray-100 text-xs truncate" title={c.name}>{c.name || "—"}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-gray-900 dark:text-gray-100 text-xs truncate" title={c.role}>{c.role || "—"}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-gray-900 dark:text-gray-100 text-xs truncate" title={c.email}>{c.email || "—"}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-center">
                      {c.linkedin ? (
                        <a href={c.linkedin} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline text-xs">
                          View
                        </a>
                      ) : (
                        <span className="text-gray-500 dark:text-gray-400">—</span>
                      )}
                    </td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-gray-900 dark:text-gray-100 text-xs truncate" title={c.phone}>{c.phone || "—"}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-gray-900 dark:text-gray-100 text-xs truncate" title={c.leadSource}>{c.leadSource || "—"}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-gray-900 dark:text-gray-100 text-xs truncate" title={c.company}>{c.company || "—"}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-gray-900 dark:text-gray-100 text-xs truncate" title={c.city}>{c.city || "—"}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-gray-900 dark:text-gray-100 text-xs truncate" title={c.industry}>{c.industry || "—"}</td>
                    <td className="border border-gray-300 dark:border-gray-600 px-2 py-2 text-center">
                      <div className="flex gap-1 justify-center">
                        <button className="bg-yellow-400 hover:bg-yellow-500 text-black px-1 py-1 rounded text-xs" onClick={()=>startEdit(c)}>Edit</button>
                        {c.phone && (
                          <button 
                            className="bg-green-600 hover:bg-green-700 text-white px-1 py-1 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed" 
                            onClick={() => sendWhatsAppInviteToContact(c)}
                            disabled={sendingWhatsAppInvite === c.id}
                            title={`Send WhatsApp invite to ${c.name || c.email}`}
                          >
                            {sendingWhatsAppInvite === c.id ? '⏳' : '📱'}
                          </button>
                        )}
                        <button className="bg-red-600 hover:bg-red-700 text-white px-1 py-1 rounded text-xs" onClick={()=>deleteContact(c.id)}>Del</button>
                      </div>
                    </td>
                  </tr>
                  {editingId === c.id && (
                    <tr className="bg-gray-50 dark:bg-gray-900">
                      <td colSpan={10} className="border border-gray-300 dark:border-gray-600 px-3 py-3">
                        <div className="grid grid-cols-3 gap-2">
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Name" value={editForm.name || ''} onChange={e=>setEditForm(prev=>({...prev,name:e.target.value}))} />
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Role" value={editForm.role || ''} onChange={e=>setEditForm(prev=>({...prev,role:e.target.value}))} />
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Email" value={editForm.email || ''} onChange={e=>setEditForm(prev=>({...prev,email:e.target.value}))} />
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="LinkedIn" value={editForm.linkedin || ''} onChange={e=>setEditForm(prev=>({...prev,linkedin:e.target.value}))} />
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Phone" value={editForm.phone || ''} onChange={e=>setEditForm(prev=>({...prev,phone:e.target.value}))} />
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Lead Source" value={editForm.leadSource || ''} onChange={e=>setEditForm(prev=>({...prev,leadSource:e.target.value}))} />
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Company" value={editForm.company || ''} onChange={e=>setEditForm(prev=>({...prev,company:e.target.value}))} />
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="City" value={editForm.city || ''} onChange={e=>setEditForm(prev=>({...prev,city:e.target.value}))} />
                          <input className="border border-gray-300 dark:border-gray-600 p-1 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs" placeholder="Industry" value={editForm.industry || ''} onChange={e=>setEditForm(prev=>({...prev,industry:e.target.value}))} />
                        </div>
                        <div className="mt-2 flex gap-2">
                          <button className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs" onClick={()=>saveEdit(c.id)}>Save</button>
                          <button className="bg-gray-500 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs" onClick={cancelEdit}>Cancel</button>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Pagination Controls */}
      {totalContacts > pageSize && (
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Page {currentPage + 1} of {Math.ceil(totalContacts / pageSize)} 
            ({(currentPage * pageSize) + 1}-{Math.min((currentPage + 1) * pageSize, totalContacts)} of {totalContacts})
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => setCurrentPage(p => Math.max(0, p - 1))} 
              disabled={currentPage === 0}
              className="bg-gray-500 text-white px-3 py-1 rounded disabled:opacity-50 hover:bg-gray-600"
            >
              Previous
            </button>
            <button 
              onClick={() => setCurrentPage(p => p + 1)} 
              disabled={(currentPage + 1) * pageSize >= totalContacts}
              className="bg-gray-500 text-white px-3 py-1 rounded disabled:opacity-50 hover:bg-gray-600"
            >
              Next
            </button>
          </div>
        </div>
      )}
      
      <div className="mt-3">
        <button className="bg-indigo-600 text-white px-3 py-1 rounded" onClick={toggleInlineAdd}>{showInlineAdd ? 'Hide' : 'Add inline'}</button>
      </div>

      {/* Enhanced Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">Advanced Contact Deletion</h3>
              <button 
                onClick={() => setShowDeleteModal(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>

            {/* Filter Controls */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {/* Industry Filter */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">Industries</label>
                <select 
                  multiple 
                  className="w-full border rounded p-2 h-24 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                  value={deleteFilters.industries}
                  onChange={(e) => setDeleteFilters(prev => ({
                    ...prev, 
                    industries: Array.from(e.target.selectedOptions, option => option.value)
                  }))}
                >
                  {availableFilters.industries.map(industry => (
                    <option key={industry} value={industry}>{industry}</option>
                  ))}
                </select>
                <div className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</div>
              </div>

              {/* Source Filter */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">Lead Sources</label>
                <select 
                  multiple 
                  className="w-full border rounded p-2 h-24 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                  value={deleteFilters.sources}
                  onChange={(e) => setDeleteFilters(prev => ({
                    ...prev,
                    sources: Array.from(e.target.selectedOptions, option => option.value)
                  }))}
                >
                  {availableFilters.sources.map(source => (
                    <option key={source} value={source}>{source}</option>
                  ))}
                </select>
                <div className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</div>
              </div>

              {/* Company Filter */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">Companies</label>
                <select 
                  multiple 
                  className="w-full border rounded p-2 h-24 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                  value={deleteFilters.companies}
                  onChange={(e) => setDeleteFilters(prev => ({
                    ...prev,
                    companies: Array.from(e.target.selectedOptions, option => option.value)
                  }))}
                >
                  {availableFilters.companies.map(company => (
                    <option key={company} value={company}>{company}</option>
                  ))}
                </select>
              </div>

              {/* City Filter */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">Cities</label>
                <select 
                  multiple 
                  className="w-full border rounded p-2 h-24 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                  value={deleteFilters.cities}
                  onChange={(e) => setDeleteFilters(prev => ({
                    ...prev,
                    cities: Array.from(e.target.selectedOptions, option => option.value)
                  }))}
                >
                  {availableFilters.cities.map(city => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </div>

              {/* Email Domain Filter */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">Email Domains</label>
                <select 
                  multiple 
                  className="w-full border rounded p-2 h-24 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                  value={deleteFilters.emailDomains}
                  onChange={(e) => setDeleteFilters(prev => ({
                    ...prev,
                    emailDomains: Array.from(e.target.selectedOptions, option => option.value)
                  }))}
                >
                  {availableFilters.emailDomains.map(domain => (
                    <option key={domain} value={domain}>@{domain}</option>
                  ))}
                </select>
              </div>

              {/* Phone & LinkedIn Filters */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">Contact Data</label>
                <div className="space-y-2">
                  <select 
                    className="w-full border rounded p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                    value={deleteFilters.hasPhone === null ? '' : deleteFilters.hasPhone ? 'true' : 'false'}
                    onChange={(e) => setDeleteFilters(prev => ({
                      ...prev,
                      hasPhone: e.target.value === '' ? null : e.target.value === 'true'
                    }))}
                  >
                    <option value="">Phone - Any</option>
                    <option value="true">Has Phone Number</option>
                    <option value="false">No Phone Number</option>
                  </select>

                  <select 
                    className="w-full border rounded p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                    value={deleteFilters.hasLinkedIn === null ? '' : deleteFilters.hasLinkedIn ? 'true' : 'false'}
                    onChange={(e) => setDeleteFilters(prev => ({
                      ...prev,
                      hasLinkedIn: e.target.value === '' ? null : e.target.value === 'true'
                    }))}
                  >
                    <option value="">LinkedIn - Any</option>
                    <option value="true">Has LinkedIn</option>
                    <option value="false">No LinkedIn</option>
                  </select>
                </div>
              </div>

              {/* Search Text Filter */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-gray-100">Search Text</label>
                <input 
                  type="text"
                  className="w-full border rounded p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100"
                  placeholder="Search name, email, company, role, or source"
                  value={deleteFilters.searchText}
                  onChange={(e) => setDeleteFilters(prev => ({
                    ...prev,
                    searchText: e.target.value
                  }))}
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 mb-4">
              <button 
                onClick={generateDeletePreview}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Preview Deletion
              </button>
              <button 
                onClick={() => setDeleteFilters({
                  industries: [],
                  companies: [],
                  cities: [],
                  emailDomains: [],
                  sources: [],
                  hasPhone: null,
                  hasLinkedIn: null,
                  dateRange: { from: '', to: '' },
                  searchText: ''
                })}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                Clear Filters
              </button>
            </div>

            {/* Preview Results */}
            {deletePreview && (
              <div className="border rounded p-4 bg-gray-50 dark:bg-gray-700 mb-4">
                <h4 className="font-bold mb-2 text-red-700 dark:text-red-300">
                  ⚠️ {deletePreview.count} contacts will be deleted
                </h4>
                
                {deletePreview.count > 0 && (
                  <>
                    {/* Statistics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                      {Object.entries(deletePreview.breakdown).map(([key, value]) => (
                        <div key={key} className="text-sm">
                          <span className="font-medium">{key}:</span> {value}
                        </div>
                      ))}
                    </div>

                    {/* Sample Contacts */}
                    <div className="mb-4">
                      <h5 className="font-medium mb-2">Sample contacts to be deleted:</h5>
                      <div className="max-h-40 overflow-y-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="bg-gray-100 dark:bg-gray-600">
                              <th className="text-left p-1">Name</th>
                              <th className="text-left p-1">Email</th>
                              <th className="text-left p-1">Company</th>
                              <th className="text-left p-1">Industry</th>
                            </tr>
                          </thead>
                          <tbody>
                            {deletePreview.contacts.map((contact, index) => (
                              <tr key={index} className="border-b">
                                <td className="p-1">{contact.name}</td>
                                <td className="p-1">{contact.email}</td>
                                <td className="p-1">{contact.company}</td>
                                <td className="p-1">{contact.industry}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {deletePreview.count > 10 && (
                          <div className="text-xs text-gray-500 mt-2">
                            Showing first 10 of {deletePreview.count} contacts
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Company Cleanup Option */}
                    <div className="mb-4 p-3 border rounded bg-yellow-50 dark:bg-yellow-900/20">
                      <label className="flex items-center gap-2 text-sm">
                        <input 
                          type="checkbox"
                          checked={cleanupOrphanedCompanies}
                          onChange={(e) => setCleanupOrphanedCompanies(e.target.checked)}
                          className="rounded"
                        />
                        <span className="font-medium">Also clean up orphaned companies</span>
                      </label>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        Remove companies that will have no contacts after this deletion
                      </p>
                    </div>

                    {/* Delete Button */}
                    <button 
                      onClick={executeBulkDelete}
                      disabled={deletingBulk}
                      className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 disabled:opacity-50"
                    >
                      {deletingBulk ? 'Deleting...' : `Delete ${deletePreview.count} Contacts`}
                    </button>
                  </>
                )}

                {deletePreview.count === 0 && (
                  <div className="text-gray-600">No contacts match the selected filters.</div>
                )}
              </div>
            )}

            {/* Quick Actions */}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-2">Quick Delete Options</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                <button 
                  onClick={() => {
                    setDeleteFilters(prev => ({ ...prev, hasPhone: false }));
                    setTimeout(generateDeletePreview, 100);
                  }}
                  className="bg-orange-500 text-white text-xs px-2 py-1 rounded hover:bg-orange-600"
                >
                  Contacts w/o Phone
                </button>
                <button 
                  onClick={() => {
                    setDeleteFilters(prev => ({ ...prev, hasLinkedIn: false }));
                    setTimeout(generateDeletePreview, 100);
                  }}
                  className="bg-orange-500 text-white text-xs px-2 py-1 rounded hover:bg-orange-600"
                >
                  Contacts w/o LinkedIn
                </button>
                <button 
                  onClick={() => {
                    setDeleteFilters(prev => ({ ...prev, industries: [''] }));
                    setTimeout(generateDeletePreview, 100);
                  }}
                  className="bg-orange-500 text-white text-xs px-2 py-1 rounded hover:bg-orange-600"
                >
                  No Industry Set
                </button>
                <button 
                  onClick={() => {
                    setDeleteFilters(prev => ({ ...prev, companies: [''] }));
                    setTimeout(generateDeletePreview, 100);
                  }}
                  className="bg-orange-500 text-white text-xs px-2 py-1 rounded hover:bg-orange-600"
                >
                  No Company Set
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

  {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  );
}
