(()=>{var l={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};var x=([e,o,a])=>{let t=document.createElementNS("http://www.w3.org/2000/svg",e);return Object.keys(o).forEach(r=>{t.setAttribute(r,String(o[r]))}),a?.length&&a.forEach(r=>{let f=x(r);t.appendChild(f)}),t},i=(e,o={})=>{let a="svg",t={...l,...o};return x([a,t,e])};var C=e=>Array.from(e.attributes).reduce((o,a)=>(o[a.name]=a.value,o),{}),S=e=>typeof e=="string"?e:!e||!e.class?"":e.class&&typeof e.class=="string"?e.class.split(" "):e.class&&Array.isArray(e.class)?e.class:"",h=e=>e.flatMap(S).map(a=>a.trim()).filter(Boolean).filter((a,t,r)=>r.indexOf(a)===t).join(" "),g=e=>e.replace(/(\w)(\w*)(_|-|\s*)/g,(o,a,t)=>a.toUpperCase()+t.toLowerCase()),s=(e,{nameAttr:o,icons:a,attrs:t})=>{let r=e.getAttribute(o);if(r==null)return;let f=g(r),u=a[f];if(!u)return console.warn(`${e.outerHTML} icon name was not found in the provided icons object.`);let d=C(e),p={...l,"data-lucide":r,...t,...d},m=h(["lucide",`lucide-${r}`,d,t]);m&&Object.assign(p,{class:m});let c=i(u,p);return e.parentNode?.replaceChild(c,e)};var n=({icons:e={},nameAttr:o="data-lucide",attrs:a={}}={})=>{if(!Object.values(e).length)throw new Error(`Please provide an icons object.
If you want to use all the icons you can import it like:
 \`import { createIcons, icons } from 'lucide';
lucide.createIcons({icons});\``);if(typeof document>"u")throw new Error("`createIcons()` only works in a browser environment.");let t=document.querySelectorAll(`[${o}]`);if(Array.from(t).forEach(r=>s(r,{nameAttr:o,icons:e,attrs:a})),o==="data-lucide"){let r=document.querySelectorAll("[icon-name]");r.length>0&&(console.warn("[Lucide] Some icons were found with the now deprecated icon-name attribute. These will still be replaced for backwards compatibility, but will no longer be supported in v1.0 and you should switch to data-lucide"),Array.from(r).forEach(f=>s(f,{nameAttr:"icon-name",icons:e,attrs:a})))}};n({icons:{}});})();
/*! Bundled license information:

lucide/dist/esm/defaultAttributes.js:
lucide/dist/esm/createElement.js:
lucide/dist/esm/replaceElement.js:
lucide/dist/esm/lucide.js:
  (**
   * @license lucide v0.507.0 - ISC
   *
   * This source code is licensed under the ISC license.
   * See the LICENSE file in the root directory of this source tree.
   *)
*/
