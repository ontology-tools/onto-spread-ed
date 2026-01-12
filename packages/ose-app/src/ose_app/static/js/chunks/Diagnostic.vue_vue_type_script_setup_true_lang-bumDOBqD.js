import{d as m,l,c as n,f as d,a as r,F as c,e as a,s as g,h as $,t as p}from"./filter-CdAXK93b.js";const s={"unknown-parent":{severity:"error",title:e=>"Unknown parent",message:e=>`The parent <code>${e.parent.label}</code> of <code>${(e.term??e.relation).label}</code>
              (<code>${(e.term??e.relation).id||"no id"}</code>) is not known.`},"missing-parent":{severity:"error",title:e=>"Missing parent",message:e=>`The parent <code>${e.parent.label}</code> (<code>${e.parent.id}</code>) of
              <code>${e.term.label}</code>
              (<code>${e.term.id||"no id"}</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${e.parent.label} [${e.parent.id}]</code>.`},"no-parent":{severity:"error",title:e=>"Term has no parent",message:e=>`The term <code>${e.term.label}</code> (<code>${e.term.id??"no id"}</code>) has no parent!`},"ignored-parent":{severity:"error",title:e=>`${e.status} parent`,message:e=>`The parent <code>${e.parent.label}</code> of <code>${e.term.label}</code>
              (<code>${e.term.id??"no id"}</code>) is ${e.status.toLowerCase()}.<br>`},"missing-label":{severity:"error",title:e=>"Missing label",message:e=>`The term <code>${e.term.id}</code> has no label.`},"missing-id":{severity:"error",title:e=>"Term has no ID",message:e=>`              The term <code>${e.term.label}</code> has no ID but is also not obsolete or pre-proposed. <br>`},"unknown-disjoint":{severity:"error",title:e=>"Unknown disjoint class",message:e=>`The class <code>${e.term.label}</code> (<code>${e.term.id??"no id"}</code>) is
              specified to
              be disjoint with <code>${e.disjoint_class.label}</code> but it is not known.<br>`},"missing-disjoint":{severity:"error",title:e=>"Missing disjoint class",message:e=>`The disjoint class <code>${e.disjoint_class.label}</code> (<code>${e.disjoint_class.id}</code>) of 
              <code>${e.term.label}</code>
              (<code>${e.term.id||"no id"}</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${e.disjoint_class.label} [${e.disjoint_class.id}]</code>.`},"ignored-disjoint":{severity:"error",title:e=>`${e.status} disjoint class`,message:e=>`The disjoint class <code>${e.disjoint_class.label}</code> of <code>${e.term.label}</code>
              (<code>${e.term.id??"no id"}</code>) is ${e.status.toLowerCase()}.<br>`},"unknown-relation-value":{severity:"error",title:e=>`Unknown value for relation <code>${e.relation.label}</code>`,message:e=>`Related term <code>${e.value.label}</code> of <code>${e.term.label}</code>
              (<code>${e.term.id||"no id"}
            </code>) for <code>${e.relation.label}</code> is not known.`},"missing-relation-value":{severity:"error",title:e=>`Unknown value for relation <code>${e.relation.label}</code>`,message:e=>`Related term <code>${e.value.label}</code> of 
              <code>${e.term.label}</code>
              (<code>${e.term.id||"no id"}</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${e.value.label} [${e.value.id}]</code>.`},"ignored-relation-value":{severity:"error",title:e=>`${e.status} value for relation <code>${e.relation.label}</code>`,message:e=>`Related term <code>${e.value.label}</code> of <code>${e.term.label}</code>
              (<code>${e.term.id??"no id"}</code>) is ${e.status.toLowerCase()}.`},"unknown-range":{severity:"error",title:e=>"Unknown range",message:e=>`The range <code>${e.relation.range.label}</code> of
              <code>${e.relation.label}</code>
              (<code>${e.relation.id||"no id"}
            </code>) is not known. `},"missing-range":{severity:"error",title:e=>"Missing range",message:e=>`The range <code>${e.relation.range.label}</code> of 
              <code>${e.relation.label}</code>
              (<code>${e.relation.id||"no id"}</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${e.range.label} [${e.range.id}]</code>.`},"ignored-range":{severity:"error",title:e=>`${e.status} range`,message:e=>`The range <code>${e.range.label}</code> of <code>${e.relation.label}</code>
              (<code>${e.relation.id??"no id"}</code>) is ${e.status.toLowerCase()}.<br>`},"unknown-domain":{severity:"error",title:e=>"Unknown domain",message:e=>`The domain <code>${e.relation.domain.label}</code> of
              <code>${e.relation.label}</code>
              (<code>${e.relation.id||"no id"} </code>) is not known.`},"missing-domain":{severity:"error",title:e=>"Missing domain",message:e=>`The domain <code>${e.relation.domain.label}</code> of 
              <code>${e.relation.label}</code>
              (<code>${e.relation.id||"no id"}</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${e.domain.label} [${e.domain.id}]</code>.`},"ignored-domain":{severity:"error",title:e=>`${e.status} domain`,message:e=>`The domain <code>${e.domain.label}</code> of <code>${e.relation.label}</code>
              (<code>${e.relation.id??"no id"}</code>) is ${e.status.toLowerCase()}.<br>`},"unknown-relation":{severity:"error",title:e=>"Unknown relation",message:e=>`The relation ${e.relation.label?`<code>${e.relation.label}</code>`+(e.relation.id?"("+e.relation.id+")":""):e.relation.id} is not known`},duplicate:{severity:"error",title:e=>"Conflicting entries (duplicates)",message:e=>`There are multiple terms for the ${e.duplicate_field} <code>${e.duplicate_value}</code>:`},"incomplete-term":{severity:"warning",title:e=>"Incomplete term",message:e=>`There is an incomplete term with no an ID, a label, or a parent defined. Is there an empty line in the
              spreadsheet? The line is ignored`},"unknown-column":{severity:"warning",title:e=>"Unmapped column",message:e=>`The column <code>${e.column}</code> of <code>${e.sheet}</code> is not mapped
              to any OWL property or internal field.`},"missing-import":{severity:"warning",title:e=>"Missing import",message:e=>`The term <code>${e.term.label}</code> (<code>${e.term.id??"no id"}</code>) has the curation
              status
              "External" but is not included in the externally imported terms.`+(e.term.id?` Does the term still exist in
                ${e.term.id.split(":")[0]}?`:"")},"inconsistent-import":{severity:"warning",title:e=>"Inconsistent import",message:e=>`The term <code>${e.term.label}</code> (<code>${e.term.id??"no id"}</code>) has the curation
              status "External" but its `+(e.term.id!==e.imported_term.id?`ID (<code>${e.imported_term.id}</code>)`:`label (<code>${e.imported_term.label}</code>)`)+" differs."}},h=["innerHTML"],u=["innerHTML"],b={key:0},f={key:1},v=["innerHTML"],T=m({__name:"Diagnostic",props:{diagnostic:{},severity:{default:null},format:{default:"long"}},setup(e){const t=e;l(()=>({"text-bg-danger":(t.severity??o.value.severity)==="error","text-bg-warning":(t.severity??o.value.severity)==="warning","text-bg-info":(t.severity??o.value.severity)==="info"}));const o=l(()=>({severity:s[t.diagnostic.type].severity,title:s[t.diagnostic.type].title(t.diagnostic),message:s[t.diagnostic.type].message(t.diagnostic)}));return(i,y)=>i.format==="long"?(r(),n(c,{key:0},[a("h5",{innerHTML:o.value.title},null,8,h),a("p",{innerHTML:o.value.message},null,8,u),i.$slots.default?(r(),n("p",b,[g(i.$slots,"default")])):d("",!0)],64)):i.format==="inline"?(r(),n("p",f,[a("span",{innerHTML:o.value.message},null,8,v)])):i.format==="text"?(r(),n(c,{key:2},[$(p(o.value.message.replace(/(<([^>]+)>)/ig,"")),1)],64)):d("",!0)}});export{s as D,T as _};
//# sourceMappingURL=Diagnostic.vue_vue_type_script_setup_true_lang-bumDOBqD.js.map
