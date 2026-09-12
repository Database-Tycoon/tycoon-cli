var Xd=Object.defineProperty;var qd=(i,e,t)=>e in i?Xd(i,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):i[e]=t;var Q=(i,e,t)=>qd(i,typeof e!="symbol"?e+"":e,t);(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))n(s);new MutationObserver(s=>{for(const r of s)if(r.type==="childList")for(const a of r.addedNodes)a.tagName==="LINK"&&a.rel==="modulepreload"&&n(a)}).observe(document,{childList:!0,subtree:!0});function t(s){const r={};return s.integrity&&(r.integrity=s.integrity),s.referrerPolicy&&(r.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?r.credentials="include":s.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function n(s){if(s.ep)return;s.ep=!0;const r=t(s);fetch(s.href,r)}})();/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const Cl="185",ps={ROTATE:0,DOLLY:1,PAN:2},us={ROTATE:0,PAN:1,DOLLY_PAN:2,DOLLY_ROTATE:3},Yd=0,gc=1,Zd=2,Jr=1,Kd=2,Zs=3,vi=0,rn=1,pn=2,Yn=0,ms=1,_c=2,vc=3,xc=4,jd=5,Ii=100,Jd=101,Qd=102,ef=103,tf=104,nf=200,sf=201,rf=202,af=203,wo=204,To=205,of=206,lf=207,cf=208,hf=209,uf=210,df=211,ff=212,pf=213,mf=214,Ao=0,Ro=1,Co=2,ys=3,Po=4,Lo=5,Do=6,Io=7,Pl=0,gf=1,_f=2,In=0,Cu=1,Pu=2,Lu=3,Du=4,Iu=5,Nu=6,Uu=7,Ou=300,Fi=301,bs=302,Ca=303,Pa=304,ba=306,tr=1e3,Wn=1001,No=1002,Mt=1003,vf=1004,mr=1005,Zt=1006,La=1007,$n=1008,hn=1009,Fu=1010,ku=1011,nr=1012,Ll=1013,On=1014,bn=1015,Kn=1016,Dl=1017,Il=1018,ir=1020,Bu=35902,zu=35899,Hu=1021,Vu=1022,gn=1023,jn=1026,Ui=1027,lr=1028,Nl=1029,ki=1030,Ul=1031,Ol=1033,Qr=33776,ea=33777,ta=33778,na=33779,Uo=35840,Oo=35841,Fo=35842,ko=35843,Bo=36196,zo=37492,Ho=37496,Vo=37488,Go=37489,ra=37490,Wo=37491,$o=37808,Xo=37809,qo=37810,Yo=37811,Zo=37812,Ko=37813,jo=37814,Jo=37815,Qo=37816,el=37817,tl=37818,nl=37819,il=37820,sl=37821,rl=36492,al=36494,ol=36495,ll=36283,cl=36284,aa=36285,hl=36286,xf=3200,ul=0,yf=1,Gn="",sn="srgb",oa="srgb-linear",la="linear",ft="srgb",Wi=7680,yc=519,bf=512,Mf=513,Sf=514,Fl=515,Ef=516,wf=517,kl=518,Tf=519,bc=35044,Mc="300 es",Dn=2e3,sr=2001;function Af(i){for(let e=i.length-1;e>=0;--e)if(i[e]>=65535)return!0;return!1}function ca(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function Rf(){const i=ca("canvas");return i.style.display="block",i}const Sc={};function Ec(...i){const e="THREE."+i.shift();console.log(e,...i)}function Gu(i){const e=i[0];if(typeof e=="string"&&e.startsWith("TSL:")){const t=i[1];t&&t.isStackTrace?i[0]+=" "+t.getLocation():i[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return i}function ke(...i){i=Gu(i);const e="THREE."+i.shift();{const t=i[0];t&&t.isStackTrace?console.warn(t.getError(e)):console.warn(e,...i)}}function st(...i){i=Gu(i);const e="THREE."+i.shift();{const t=i[0];t&&t.isStackTrace?console.error(t.getError(e)):console.error(e,...i)}}function gs(...i){const e=i.join(" ");e in Sc||(Sc[e]=!0,ke(...i))}function Cf(i,e,t){return new Promise(function(n,s){function r(){switch(i.clientWaitSync(e,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:s();break;case i.TIMEOUT_EXPIRED:setTimeout(r,t);break;default:n()}}setTimeout(r,t)})}const Pf={[Ao]:Ro,[Co]:Do,[Po]:Io,[ys]:Lo,[Ro]:Ao,[Do]:Co,[Io]:Po,[Lo]:ys};class Ei{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});const n=this._listeners;n[e]===void 0&&(n[e]=[]),n[e].indexOf(t)===-1&&n[e].push(t)}hasEventListener(e,t){const n=this._listeners;return n===void 0?!1:n[e]!==void 0&&n[e].indexOf(t)!==-1}removeEventListener(e,t){const n=this._listeners;if(n===void 0)return;const s=n[e];if(s!==void 0){const r=s.indexOf(t);r!==-1&&s.splice(r,1)}}dispatchEvent(e){const t=this._listeners;if(t===void 0)return;const n=t[e.type];if(n!==void 0){e.target=this;const s=n.slice(0);for(let r=0,a=s.length;r<a;r++)s[r].call(this,e);e.target=null}}}const qt=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Qs=Math.PI/180,dl=180/Math.PI;function cr(){const i=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,n=Math.random()*4294967295|0;return(qt[i&255]+qt[i>>8&255]+qt[i>>16&255]+qt[i>>24&255]+"-"+qt[e&255]+qt[e>>8&255]+"-"+qt[e>>16&15|64]+qt[e>>24&255]+"-"+qt[t&63|128]+qt[t>>8&255]+"-"+qt[t>>16&255]+qt[t>>24&255]+qt[n&255]+qt[n>>8&255]+qt[n>>16&255]+qt[n>>24&255]).toLowerCase()}function Qe(i,e,t){return Math.max(e,Math.min(t,i))}function Lf(i,e){return(i%e+e)%e}function Da(i,e,t){return(1-t)*i+t*e}function Os(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function tn(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}const Df={DEG2RAD:Qs},nc=class nc{constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("THREE.Vector2: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const t=this.x,n=this.y,s=e.elements;return this.x=s[0]*t+s[3]*n+s[6],this.y=s[1]*t+s[4]*n+s[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=Qe(this.x,e.x,t.x),this.y=Qe(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=Qe(this.x,e,t),this.y=Qe(this.y,e,t),this}clampLength(e,t){const n=this.length();return this.divideScalar(n||1).multiplyScalar(Qe(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const n=this.dot(e)/t;return Math.acos(Qe(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,n=this.y-e.y;return t*t+n*n}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){const n=Math.cos(t),s=Math.sin(t),r=this.x-e.x,a=this.y-e.y;return this.x=r*n-a*s+e.x,this.y=r*s+a*n+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};nc.prototype.isVector2=!0;let Fe=nc;class Sn{constructor(e=0,t=0,n=0,s=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=n,this._w=s}static slerpFlat(e,t,n,s,r,a,o){let l=n[s+0],c=n[s+1],h=n[s+2],d=n[s+3],u=r[a+0],p=r[a+1],g=r[a+2],x=r[a+3];if(d!==x||l!==u||c!==p||h!==g){let m=l*u+c*p+h*g+d*x;m<0&&(u=-u,p=-p,g=-g,x=-x,m=-m);let f=1-o;if(m<.9995){const M=Math.acos(m),E=Math.sin(M);f=Math.sin(f*M)/E,o=Math.sin(o*M)/E,l=l*f+u*o,c=c*f+p*o,h=h*f+g*o,d=d*f+x*o}else{l=l*f+u*o,c=c*f+p*o,h=h*f+g*o,d=d*f+x*o;const M=1/Math.sqrt(l*l+c*c+h*h+d*d);l*=M,c*=M,h*=M,d*=M}}e[t]=l,e[t+1]=c,e[t+2]=h,e[t+3]=d}static multiplyQuaternionsFlat(e,t,n,s,r,a){const o=n[s],l=n[s+1],c=n[s+2],h=n[s+3],d=r[a],u=r[a+1],p=r[a+2],g=r[a+3];return e[t]=o*g+h*d+l*p-c*u,e[t+1]=l*g+h*u+c*d-o*p,e[t+2]=c*g+h*p+o*u-l*d,e[t+3]=h*g-o*d-l*u-c*p,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,n,s){return this._x=e,this._y=t,this._z=n,this._w=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){const n=e._x,s=e._y,r=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(n/2),h=o(s/2),d=o(r/2),u=l(n/2),p=l(s/2),g=l(r/2);switch(a){case"XYZ":this._x=u*h*d+c*p*g,this._y=c*p*d-u*h*g,this._z=c*h*g+u*p*d,this._w=c*h*d-u*p*g;break;case"YXZ":this._x=u*h*d+c*p*g,this._y=c*p*d-u*h*g,this._z=c*h*g-u*p*d,this._w=c*h*d+u*p*g;break;case"ZXY":this._x=u*h*d-c*p*g,this._y=c*p*d+u*h*g,this._z=c*h*g+u*p*d,this._w=c*h*d-u*p*g;break;case"ZYX":this._x=u*h*d-c*p*g,this._y=c*p*d+u*h*g,this._z=c*h*g-u*p*d,this._w=c*h*d+u*p*g;break;case"YZX":this._x=u*h*d+c*p*g,this._y=c*p*d+u*h*g,this._z=c*h*g-u*p*d,this._w=c*h*d-u*p*g;break;case"XZY":this._x=u*h*d-c*p*g,this._y=c*p*d-u*h*g,this._z=c*h*g+u*p*d,this._w=c*h*d+u*p*g;break;default:ke("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){const n=t/2,s=Math.sin(n);return this._x=e.x*s,this._y=e.y*s,this._z=e.z*s,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(e){const t=e.elements,n=t[0],s=t[4],r=t[8],a=t[1],o=t[5],l=t[9],c=t[2],h=t[6],d=t[10],u=n+o+d;if(u>0){const p=.5/Math.sqrt(u+1);this._w=.25/p,this._x=(h-l)*p,this._y=(r-c)*p,this._z=(a-s)*p}else if(n>o&&n>d){const p=2*Math.sqrt(1+n-o-d);this._w=(h-l)/p,this._x=.25*p,this._y=(s+a)/p,this._z=(r+c)/p}else if(o>d){const p=2*Math.sqrt(1+o-n-d);this._w=(r-c)/p,this._x=(s+a)/p,this._y=.25*p,this._z=(l+h)/p}else{const p=2*Math.sqrt(1+d-n-o);this._w=(a-s)/p,this._x=(r+c)/p,this._y=(l+h)/p,this._z=.25*p}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let n=e.dot(t)+1;return n<1e-8?(n=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=n):(this._x=0,this._y=-e.z,this._z=e.y,this._w=n)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=n),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(Qe(this.dot(e),-1,1)))}rotateTowards(e,t){const n=this.angleTo(e);if(n===0)return this;const s=Math.min(1,t/n);return this.slerp(e,s),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){const n=e._x,s=e._y,r=e._z,a=e._w,o=t._x,l=t._y,c=t._z,h=t._w;return this._x=n*h+a*o+s*c-r*l,this._y=s*h+a*l+r*o-n*c,this._z=r*h+a*c+n*l-s*o,this._w=a*h-n*o-s*l-r*c,this._onChangeCallback(),this}slerp(e,t){let n=e._x,s=e._y,r=e._z,a=e._w,o=this.dot(e);o<0&&(n=-n,s=-s,r=-r,a=-a,o=-o);let l=1-t;if(o<.9995){const c=Math.acos(o),h=Math.sin(c);l=Math.sin(l*c)/h,t=Math.sin(t*c)/h,this._x=this._x*l+n*t,this._y=this._y*l+s*t,this._z=this._z*l+r*t,this._w=this._w*l+a*t,this._onChangeCallback()}else this._x=this._x*l+n*t,this._y=this._y*l+s*t,this._z=this._z*l+r*t,this._w=this._w*l+a*t,this.normalize();return this}slerpQuaternions(e,t,n){return this.copy(e).slerp(t,n)}random(){const e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),n=Math.random(),s=Math.sqrt(1-n),r=Math.sqrt(n);return this.set(s*Math.sin(e),s*Math.cos(e),r*Math.sin(t),r*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}const ic=class ic{constructor(e=0,t=0,n=0){this.x=e,this.y=t,this.z=n}set(e,t,n){return n===void 0&&(n=this.z),this.x=e,this.y=t,this.z=n,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("THREE.Vector3: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(wc.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(wc.setFromAxisAngle(e,t))}applyMatrix3(e){const t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[3]*n+r[6]*s,this.y=r[1]*t+r[4]*n+r[7]*s,this.z=r[2]*t+r[5]*n+r[8]*s,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const t=this.x,n=this.y,s=this.z,r=e.elements,a=1/(r[3]*t+r[7]*n+r[11]*s+r[15]);return this.x=(r[0]*t+r[4]*n+r[8]*s+r[12])*a,this.y=(r[1]*t+r[5]*n+r[9]*s+r[13])*a,this.z=(r[2]*t+r[6]*n+r[10]*s+r[14])*a,this}applyQuaternion(e){const t=this.x,n=this.y,s=this.z,r=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*s-o*n),h=2*(o*t-r*s),d=2*(r*n-a*t);return this.x=t+l*c+a*d-o*h,this.y=n+l*h+o*c-r*d,this.z=s+l*d+r*h-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[4]*n+r[8]*s,this.y=r[1]*t+r[5]*n+r[9]*s,this.z=r[2]*t+r[6]*n+r[10]*s,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=Qe(this.x,e.x,t.x),this.y=Qe(this.y,e.y,t.y),this.z=Qe(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=Qe(this.x,e,t),this.y=Qe(this.y,e,t),this.z=Qe(this.z,e,t),this}clampLength(e,t){const n=this.length();return this.divideScalar(n||1).multiplyScalar(Qe(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){const n=e.x,s=e.y,r=e.z,a=t.x,o=t.y,l=t.z;return this.x=s*l-r*o,this.y=r*a-n*l,this.z=n*o-s*a,this}projectOnVector(e){const t=e.lengthSq();if(t===0)return this.set(0,0,0);const n=e.dot(this)/t;return this.copy(e).multiplyScalar(n)}projectOnPlane(e){return Ia.copy(this).projectOnVector(e),this.sub(Ia)}reflect(e){return this.sub(Ia.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const n=this.dot(e)/t;return Math.acos(Qe(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,n=this.y-e.y,s=this.z-e.z;return t*t+n*n+s*s}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,n){const s=Math.sin(t)*e;return this.x=s*Math.sin(n),this.y=Math.cos(t)*e,this.z=s*Math.cos(n),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,n){return this.x=e*Math.sin(t),this.y=n,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){const t=this.setFromMatrixColumn(e,0).length(),n=this.setFromMatrixColumn(e,1).length(),s=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=n,this.z=s,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,t=Math.random()*2-1,n=Math.sqrt(1-t*t);return this.x=n*Math.cos(e),this.y=t,this.z=n*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};ic.prototype.isVector3=!0;let P=ic;const Ia=new P,wc=new Sn,sc=class sc{constructor(e,t,n,s,r,a,o,l,c){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,l,c)}set(e,t,n,s,r,a,o,l,c){const h=this.elements;return h[0]=e,h[1]=s,h[2]=o,h[3]=t,h[4]=r,h[5]=l,h[6]=n,h[7]=a,h[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],this}extractBasis(e,t,n){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[3],l=n[6],c=n[1],h=n[4],d=n[7],u=n[2],p=n[5],g=n[8],x=s[0],m=s[3],f=s[6],M=s[1],E=s[4],y=s[7],T=s[2],S=s[5],R=s[8];return r[0]=a*x+o*M+l*T,r[3]=a*m+o*E+l*S,r[6]=a*f+o*y+l*R,r[1]=c*x+h*M+d*T,r[4]=c*m+h*E+d*S,r[7]=c*f+h*y+d*R,r[2]=u*x+p*M+g*T,r[5]=u*m+p*E+g*S,r[8]=u*f+p*y+g*R,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){const e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8];return t*a*h-t*o*c-n*r*h+n*o*l+s*r*c-s*a*l}invert(){const e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8],d=h*a-o*c,u=o*l-h*r,p=c*r-a*l,g=t*d+n*u+s*p;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);const x=1/g;return e[0]=d*x,e[1]=(s*c-h*n)*x,e[2]=(o*n-s*a)*x,e[3]=u*x,e[4]=(h*t-s*l)*x,e[5]=(s*r-o*t)*x,e[6]=p*x,e[7]=(n*l-c*t)*x,e[8]=(a*t-n*r)*x,this}transpose(){let e;const t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,n,s,r,a,o){const l=Math.cos(r),c=Math.sin(r);return this.set(n*l,n*c,-n*(l*a+c*o)+a+e,-s*c,s*l,-s*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return gs("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(Na.makeScale(e,t)),this}rotate(e){return gs("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(Na.makeRotation(-e)),this}translate(e,t){return gs("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(Na.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){const t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,n,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){const t=this.elements,n=e.elements;for(let s=0;s<9;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<9;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){const n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e}clone(){return new this.constructor().fromArray(this.elements)}};sc.prototype.isMatrix3=!0;let Xe=sc;const Na=new Xe,Tc=new Xe().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Ac=new Xe().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function If(){const i={enabled:!0,workingColorSpace:oa,spaces:{},convert:function(s,r,a){return this.enabled===!1||r===a||!r||!a||(this.spaces[r].transfer===ft&&(s.r=Zn(s.r),s.g=Zn(s.g),s.b=Zn(s.b)),this.spaces[r].primaries!==this.spaces[a].primaries&&(s.applyMatrix3(this.spaces[r].toXYZ),s.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===ft&&(s.r=_s(s.r),s.g=_s(s.g),s.b=_s(s.b))),s},workingToColorSpace:function(s,r){return this.convert(s,this.workingColorSpace,r)},colorSpaceToWorking:function(s,r){return this.convert(s,r,this.workingColorSpace)},getPrimaries:function(s){return this.spaces[s].primaries},getTransfer:function(s){return s===Gn?la:this.spaces[s].transfer},getToneMappingMode:function(s){return this.spaces[s].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(s,r=this.workingColorSpace){return s.fromArray(this.spaces[r].luminanceCoefficients)},define:function(s){Object.assign(this.spaces,s)},_getMatrix:function(s,r,a){return s.copy(this.spaces[r].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(s){return this.spaces[s].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(s=this.workingColorSpace){return this.spaces[s].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(s,r){return gs("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(s,r)},toWorkingColorSpace:function(s,r){return gs("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(s,r)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[oa]:{primaries:e,whitePoint:n,transfer:la,toXYZ:Tc,fromXYZ:Ac,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:sn},outputColorSpaceConfig:{drawingBufferColorSpace:sn}},[sn]:{primaries:e,whitePoint:n,transfer:ft,toXYZ:Tc,fromXYZ:Ac,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:sn}}}),i}const et=If();function Zn(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function _s(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}let $i;class Nf{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{$i===void 0&&($i=ca("canvas")),$i.width=e.width,$i.height=e.height;const s=$i.getContext("2d");e instanceof ImageData?s.putImageData(e,0,0):s.drawImage(e,0,0,e.width,e.height),n=$i}return n.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const t=ca("canvas");t.width=e.width,t.height=e.height;const n=t.getContext("2d");n.drawImage(e,0,0,e.width,e.height);const s=n.getImageData(0,0,e.width,e.height),r=s.data;for(let a=0;a<r.length;a++)r[a]=Zn(r[a]/255)*255;return n.putImageData(s,0,0),t}else if(e.data){const t=e.data.slice(0);for(let n=0;n<t.length;n++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[n]=Math.floor(Zn(t[n]/255)*255):t[n]=Zn(t[n]);return{data:t,width:e.width,height:e.height}}else return ke("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let Uf=0;class Bl{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:Uf++}),this.uuid=cr(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayWidth,t.displayHeight,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const n={uuid:this.uuid,url:""},s=this.data;if(s!==null){let r;if(Array.isArray(s)){r=[];for(let a=0,o=s.length;a<o;a++)s[a].isDataTexture?r.push(Ua(s[a].image)):r.push(Ua(s[a]))}else r=Ua(s);n.url=r}return t||(e.images[this.uuid]=n),n}}function Ua(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?Nf.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:(ke("Texture: Unable to serialize Texture."),{})}let Of=0;const Oa=new P;class Kt extends Ei{constructor(e=Kt.DEFAULT_IMAGE,t=Kt.DEFAULT_MAPPING,n=Wn,s=Wn,r=Zt,a=$n,o=gn,l=hn,c=Kt.DEFAULT_ANISOTROPY,h=Gn){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Of++}),this.uuid=cr(),this.name="",this.source=new Bl(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=n,this.wrapT=s,this.magFilter=r,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new Fe(0,0),this.repeat=new Fe(1,1),this.center=new Fe(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new Xe,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=h,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(Oa).x}get height(){return this.source.getSize(Oa).y}get depth(){return this.source.getSize(Oa).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const t in e){const n=e[t];if(n===void 0){ke(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}const s=this[t];if(s===void 0){ke(`Texture.setValues(): property '${t}' does not exist.`);continue}s&&n&&s.isVector2&&n.isVector2||s&&n&&s.isVector3&&n.isVector3||s&&n&&s.isMatrix3&&n.isMatrix3?s.copy(n):this[t]=n}}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),t||(e.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==Ou)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case tr:e.x=e.x-Math.floor(e.x);break;case Wn:e.x=e.x<0?0:1;break;case No:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case tr:e.y=e.y-Math.floor(e.y);break;case Wn:e.y=e.y<0?0:1;break;case No:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}Kt.DEFAULT_IMAGE=null;Kt.DEFAULT_MAPPING=Ou;Kt.DEFAULT_ANISOTROPY=1;const rc=class rc{constructor(e=0,t=0,n=0,s=1){this.x=e,this.y=t,this.z=n,this.w=s}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,n,s){return this.x=e,this.y=t,this.z=n,this.w=s,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("THREE.Vector4: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const t=this.x,n=this.y,s=this.z,r=this.w,a=e.elements;return this.x=a[0]*t+a[4]*n+a[8]*s+a[12]*r,this.y=a[1]*t+a[5]*n+a[9]*s+a[13]*r,this.z=a[2]*t+a[6]*n+a[10]*s+a[14]*r,this.w=a[3]*t+a[7]*n+a[11]*s+a[15]*r,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,n,s,r;const l=e.elements,c=l[0],h=l[4],d=l[8],u=l[1],p=l[5],g=l[9],x=l[2],m=l[6],f=l[10];if(Math.abs(h-u)<.01&&Math.abs(d-x)<.01&&Math.abs(g-m)<.01){if(Math.abs(h+u)<.1&&Math.abs(d+x)<.1&&Math.abs(g+m)<.1&&Math.abs(c+p+f-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;const E=(c+1)/2,y=(p+1)/2,T=(f+1)/2,S=(h+u)/4,R=(d+x)/4,v=(g+m)/4;return E>y&&E>T?E<.01?(n=0,s=.707106781,r=.707106781):(n=Math.sqrt(E),s=S/n,r=R/n):y>T?y<.01?(n=.707106781,s=0,r=.707106781):(s=Math.sqrt(y),n=S/s,r=v/s):T<.01?(n=.707106781,s=.707106781,r=0):(r=Math.sqrt(T),n=R/r,s=v/r),this.set(n,s,r,t),this}let M=Math.sqrt((m-g)*(m-g)+(d-x)*(d-x)+(u-h)*(u-h));return Math.abs(M)<.001&&(M=1),this.x=(m-g)/M,this.y=(d-x)/M,this.z=(u-h)/M,this.w=Math.acos((c+p+f-1)/2),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=Qe(this.x,e.x,t.x),this.y=Qe(this.y,e.y,t.y),this.z=Qe(this.z,e.z,t.z),this.w=Qe(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=Qe(this.x,e,t),this.y=Qe(this.y,e,t),this.z=Qe(this.z,e,t),this.w=Qe(this.w,e,t),this}clampLength(e,t){const n=this.length();return this.divideScalar(n||1).multiplyScalar(Qe(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this.w=e.w+(t.w-e.w)*n,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};rc.prototype.isVector4=!0;let At=rc;class Ff extends Ei{constructor(e=1,t=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Zt,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},n),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=n.depth,this.scissor=new At(0,0,e,t),this.scissorTest=!1,this.viewport=new At(0,0,e,t),this.textures=[];const s={width:e,height:t,depth:n.depth},r=new Kt(s),a=n.count;for(let o=0;o<a;o++)this.textures[o]=r.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview,this.useArrayDepthTexture=n.useArrayDepthTexture}_setTextureOptions(e={}){const t={minFilter:Zt,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,n=1){if(this.width!==e||this.height!==t||this.depth!==n){this.width=e,this.height=t,this.depth=n;for(let s=0,r=this.textures.length;s<r;s++)this.textures[s].image.width=e,this.textures[s].image.height=t,this.textures[s].image.depth=n,this.textures[s].isData3DTexture!==!0&&(this.textures[s].isArrayTexture=this.textures[s].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,n=e.textures.length;t<n;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;const s=Object.assign({},e.textures[t].image);this.textures[t].source=new Bl(s)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this.multiview=e.multiview,this.useArrayDepthTexture=e.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}}class Nn extends Ff{constructor(e=1,t=1,n={}){super(e,t,n),this.isWebGLRenderTarget=!0}}class Wu extends Kt{constructor(e=null,t=1,n=1,s=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=Mt,this.minFilter=Mt,this.wrapR=Wn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class kf extends Kt{constructor(e=null,t=1,n=1,s=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=Mt,this.minFilter=Mt,this.wrapR=Wn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}const ya=class ya{constructor(e,t,n,s,r,a,o,l,c,h,d,u,p,g,x,m){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,l,c,h,d,u,p,g,x,m)}set(e,t,n,s,r,a,o,l,c,h,d,u,p,g,x,m){const f=this.elements;return f[0]=e,f[4]=t,f[8]=n,f[12]=s,f[1]=r,f[5]=a,f[9]=o,f[13]=l,f[2]=c,f[6]=h,f[10]=d,f[14]=u,f[3]=p,f[7]=g,f[11]=x,f[15]=m,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new ya().fromArray(this.elements)}copy(e){const t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],t[9]=n[9],t[10]=n[10],t[11]=n[11],t[12]=n[12],t[13]=n[13],t[14]=n[14],t[15]=n[15],this}copyPosition(e){const t=this.elements,n=e.elements;return t[12]=n[12],t[13]=n[13],t[14]=n[14],this}setFromMatrix3(e){const t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,n){return this.determinantAffine()===0?(e.set(1,0,0),t.set(0,1,0),n.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this)}makeBasis(e,t,n){return this.set(e.x,t.x,n.x,0,e.y,t.y,n.y,0,e.z,t.z,n.z,0,0,0,0,1),this}extractRotation(e){if(e.determinantAffine()===0)return this.identity();const t=this.elements,n=e.elements,s=1/Xi.setFromMatrixColumn(e,0).length(),r=1/Xi.setFromMatrixColumn(e,1).length(),a=1/Xi.setFromMatrixColumn(e,2).length();return t[0]=n[0]*s,t[1]=n[1]*s,t[2]=n[2]*s,t[3]=0,t[4]=n[4]*r,t[5]=n[5]*r,t[6]=n[6]*r,t[7]=0,t[8]=n[8]*a,t[9]=n[9]*a,t[10]=n[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){const t=this.elements,n=e.x,s=e.y,r=e.z,a=Math.cos(n),o=Math.sin(n),l=Math.cos(s),c=Math.sin(s),h=Math.cos(r),d=Math.sin(r);if(e.order==="XYZ"){const u=a*h,p=a*d,g=o*h,x=o*d;t[0]=l*h,t[4]=-l*d,t[8]=c,t[1]=p+g*c,t[5]=u-x*c,t[9]=-o*l,t[2]=x-u*c,t[6]=g+p*c,t[10]=a*l}else if(e.order==="YXZ"){const u=l*h,p=l*d,g=c*h,x=c*d;t[0]=u+x*o,t[4]=g*o-p,t[8]=a*c,t[1]=a*d,t[5]=a*h,t[9]=-o,t[2]=p*o-g,t[6]=x+u*o,t[10]=a*l}else if(e.order==="ZXY"){const u=l*h,p=l*d,g=c*h,x=c*d;t[0]=u-x*o,t[4]=-a*d,t[8]=g+p*o,t[1]=p+g*o,t[5]=a*h,t[9]=x-u*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){const u=a*h,p=a*d,g=o*h,x=o*d;t[0]=l*h,t[4]=g*c-p,t[8]=u*c+x,t[1]=l*d,t[5]=x*c+u,t[9]=p*c-g,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){const u=a*l,p=a*c,g=o*l,x=o*c;t[0]=l*h,t[4]=x-u*d,t[8]=g*d+p,t[1]=d,t[5]=a*h,t[9]=-o*h,t[2]=-c*h,t[6]=p*d+g,t[10]=u-x*d}else if(e.order==="XZY"){const u=a*l,p=a*c,g=o*l,x=o*c;t[0]=l*h,t[4]=-d,t[8]=c*h,t[1]=u*d+x,t[5]=a*h,t[9]=p*d-g,t[2]=g*d-p,t[6]=o*h,t[10]=x*d+u}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(Bf,e,zf)}lookAt(e,t,n){const s=this.elements;return on.subVectors(e,t),on.lengthSq()===0&&(on.z=1),on.normalize(),ii.crossVectors(n,on),ii.lengthSq()===0&&(Math.abs(n.z)===1?on.x+=1e-4:on.z+=1e-4,on.normalize(),ii.crossVectors(n,on)),ii.normalize(),gr.crossVectors(on,ii),s[0]=ii.x,s[4]=gr.x,s[8]=on.x,s[1]=ii.y,s[5]=gr.y,s[9]=on.y,s[2]=ii.z,s[6]=gr.z,s[10]=on.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[4],l=n[8],c=n[12],h=n[1],d=n[5],u=n[9],p=n[13],g=n[2],x=n[6],m=n[10],f=n[14],M=n[3],E=n[7],y=n[11],T=n[15],S=s[0],R=s[4],v=s[8],w=s[12],C=s[1],L=s[5],N=s[9],V=s[13],$=s[2],F=s[6],W=s[10],G=s[14],J=s[3],te=s[7],oe=s[11],me=s[15];return r[0]=a*S+o*C+l*$+c*J,r[4]=a*R+o*L+l*F+c*te,r[8]=a*v+o*N+l*W+c*oe,r[12]=a*w+o*V+l*G+c*me,r[1]=h*S+d*C+u*$+p*J,r[5]=h*R+d*L+u*F+p*te,r[9]=h*v+d*N+u*W+p*oe,r[13]=h*w+d*V+u*G+p*me,r[2]=g*S+x*C+m*$+f*J,r[6]=g*R+x*L+m*F+f*te,r[10]=g*v+x*N+m*W+f*oe,r[14]=g*w+x*V+m*G+f*me,r[3]=M*S+E*C+y*$+T*J,r[7]=M*R+E*L+y*F+T*te,r[11]=M*v+E*N+y*W+T*oe,r[15]=M*w+E*V+y*G+T*me,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){const e=this.elements,t=e[0],n=e[4],s=e[8],r=e[12],a=e[1],o=e[5],l=e[9],c=e[13],h=e[2],d=e[6],u=e[10],p=e[14],g=e[3],x=e[7],m=e[11],f=e[15],M=l*p-c*u,E=o*p-c*d,y=o*u-l*d,T=a*p-c*h,S=a*u-l*h,R=a*d-o*h;return t*(x*M-m*E+f*y)-n*(g*M-m*T+f*S)+s*(g*E-x*T+f*R)-r*(g*y-x*S+m*R)}determinantAffine(){const e=this.elements,t=e[0],n=e[4],s=e[8],r=e[1],a=e[5],o=e[9],l=e[2],c=e[6],h=e[10];return t*(a*h-o*c)-n*(r*h-o*l)+s*(r*c-a*l)}transpose(){const e=this.elements;let t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,n){const s=this.elements;return e.isVector3?(s[12]=e.x,s[13]=e.y,s[14]=e.z):(s[12]=e,s[13]=t,s[14]=n),this}invert(){const e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8],d=e[9],u=e[10],p=e[11],g=e[12],x=e[13],m=e[14],f=e[15],M=t*o-n*a,E=t*l-s*a,y=t*c-r*a,T=n*l-s*o,S=n*c-r*o,R=s*c-r*l,v=h*x-d*g,w=h*m-u*g,C=h*f-p*g,L=d*m-u*x,N=d*f-p*x,V=u*f-p*m,$=M*V-E*N+y*L+T*C-S*w+R*v;if($===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const F=1/$;return e[0]=(o*V-l*N+c*L)*F,e[1]=(s*N-n*V-r*L)*F,e[2]=(x*R-m*S+f*T)*F,e[3]=(u*S-d*R-p*T)*F,e[4]=(l*C-a*V-c*w)*F,e[5]=(t*V-s*C+r*w)*F,e[6]=(m*y-g*R-f*E)*F,e[7]=(h*R-u*y+p*E)*F,e[8]=(a*N-o*C+c*v)*F,e[9]=(n*C-t*N-r*v)*F,e[10]=(g*S-x*y+f*M)*F,e[11]=(d*y-h*S-p*M)*F,e[12]=(o*w-a*L-l*v)*F,e[13]=(t*L-n*w+s*v)*F,e[14]=(x*E-g*T-m*M)*F,e[15]=(h*T-d*E+u*M)*F,this}scale(e){const t=this.elements,n=e.x,s=e.y,r=e.z;return t[0]*=n,t[4]*=s,t[8]*=r,t[1]*=n,t[5]*=s,t[9]*=r,t[2]*=n,t[6]*=s,t[10]*=r,t[3]*=n,t[7]*=s,t[11]*=r,this}getMaxScaleOnAxis(){const e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],n=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],s=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,n,s))}makeTranslation(e,t,n){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,n,0,0,0,1),this}makeRotationX(e){const t=Math.cos(e),n=Math.sin(e);return this.set(1,0,0,0,0,t,-n,0,0,n,t,0,0,0,0,1),this}makeRotationY(e){const t=Math.cos(e),n=Math.sin(e);return this.set(t,0,n,0,0,1,0,0,-n,0,t,0,0,0,0,1),this}makeRotationZ(e){const t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,0,n,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){const n=Math.cos(t),s=Math.sin(t),r=1-n,a=e.x,o=e.y,l=e.z,c=r*a,h=r*o;return this.set(c*a+n,c*o-s*l,c*l+s*o,0,c*o+s*l,h*o+n,h*l-s*a,0,c*l-s*o,h*l+s*a,r*l*l+n,0,0,0,0,1),this}makeScale(e,t,n){return this.set(e,0,0,0,0,t,0,0,0,0,n,0,0,0,0,1),this}makeShear(e,t,n,s,r,a){return this.set(1,n,r,0,e,1,a,0,t,s,1,0,0,0,0,1),this}compose(e,t,n){const s=this.elements,r=t._x,a=t._y,o=t._z,l=t._w,c=r+r,h=a+a,d=o+o,u=r*c,p=r*h,g=r*d,x=a*h,m=a*d,f=o*d,M=l*c,E=l*h,y=l*d,T=n.x,S=n.y,R=n.z;return s[0]=(1-(x+f))*T,s[1]=(p+y)*T,s[2]=(g-E)*T,s[3]=0,s[4]=(p-y)*S,s[5]=(1-(u+f))*S,s[6]=(m+M)*S,s[7]=0,s[8]=(g+E)*R,s[9]=(m-M)*R,s[10]=(1-(u+x))*R,s[11]=0,s[12]=e.x,s[13]=e.y,s[14]=e.z,s[15]=1,this}decompose(e,t,n){const s=this.elements;e.x=s[12],e.y=s[13],e.z=s[14];const r=this.determinantAffine();if(r===0)return n.set(1,1,1),t.identity(),this;let a=Xi.set(s[0],s[1],s[2]).length();const o=Xi.set(s[4],s[5],s[6]).length(),l=Xi.set(s[8],s[9],s[10]).length();r<0&&(a=-a),vn.copy(this);const c=1/a,h=1/o,d=1/l;return vn.elements[0]*=c,vn.elements[1]*=c,vn.elements[2]*=c,vn.elements[4]*=h,vn.elements[5]*=h,vn.elements[6]*=h,vn.elements[8]*=d,vn.elements[9]*=d,vn.elements[10]*=d,t.setFromRotationMatrix(vn),n.x=a,n.y=o,n.z=l,this}makePerspective(e,t,n,s,r,a,o=Dn,l=!1){const c=this.elements,h=2*r/(t-e),d=2*r/(n-s),u=(t+e)/(t-e),p=(n+s)/(n-s);let g,x;if(l)g=r/(a-r),x=a*r/(a-r);else if(o===Dn)g=-(a+r)/(a-r),x=-2*a*r/(a-r);else if(o===sr)g=-a/(a-r),x=-a*r/(a-r);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=h,c[4]=0,c[8]=u,c[12]=0,c[1]=0,c[5]=d,c[9]=p,c[13]=0,c[2]=0,c[6]=0,c[10]=g,c[14]=x,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,n,s,r,a,o=Dn,l=!1){const c=this.elements,h=2/(t-e),d=2/(n-s),u=-(t+e)/(t-e),p=-(n+s)/(n-s);let g,x;if(l)g=1/(a-r),x=a/(a-r);else if(o===Dn)g=-2/(a-r),x=-(a+r)/(a-r);else if(o===sr)g=-1/(a-r),x=-r/(a-r);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=h,c[4]=0,c[8]=0,c[12]=u,c[1]=0,c[5]=d,c[9]=0,c[13]=p,c[2]=0,c[6]=0,c[10]=g,c[14]=x,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){const t=this.elements,n=e.elements;for(let s=0;s<16;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<16;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){const n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e[t+9]=n[9],e[t+10]=n[10],e[t+11]=n[11],e[t+12]=n[12],e[t+13]=n[13],e[t+14]=n[14],e[t+15]=n[15],e}};ya.prototype.isMatrix4=!0;let He=ya;const Xi=new P,vn=new He,Bf=new P(0,0,0),zf=new P(1,1,1),ii=new P,gr=new P,on=new P,Rc=new He,Cc=new Sn;class xi{constructor(e=0,t=0,n=0,s=xi.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=n,this._order=s}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,n,s=this._order){return this._x=e,this._y=t,this._z=n,this._order=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,n=!0){const s=e.elements,r=s[0],a=s[4],o=s[8],l=s[1],c=s[5],h=s[9],d=s[2],u=s[6],p=s[10];switch(t){case"XYZ":this._y=Math.asin(Qe(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-h,p),this._z=Math.atan2(-a,r)):(this._x=Math.atan2(u,c),this._z=0);break;case"YXZ":this._x=Math.asin(-Qe(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(o,p),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-d,r),this._z=0);break;case"ZXY":this._x=Math.asin(Qe(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(-d,p),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,r));break;case"ZYX":this._y=Math.asin(-Qe(d,-1,1)),Math.abs(d)<.9999999?(this._x=Math.atan2(u,p),this._z=Math.atan2(l,r)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(Qe(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-h,c),this._y=Math.atan2(-d,r)):(this._x=0,this._y=Math.atan2(o,p));break;case"XZY":this._z=Math.asin(-Qe(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(u,c),this._y=Math.atan2(o,r)):(this._x=Math.atan2(-h,p),this._y=0);break;default:ke("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,n===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,n){return Rc.makeRotationFromQuaternion(e),this.setFromRotationMatrix(Rc,t,n)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return Cc.setFromEuler(this),this.setFromQuaternion(Cc,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}xi.DEFAULT_ORDER="XYZ";class zl{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let Hf=0;const Pc=new P,qi=new Sn,kn=new He,_r=new P,Fs=new P,Vf=new P,Gf=new Sn,Lc=new P(1,0,0),Dc=new P(0,1,0),Ic=new P(0,0,1),Nc={type:"added"},Wf={type:"removed"},Yi={type:"childadded",child:null},Fa={type:"childremoved",child:null};class Bt extends Ei{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Hf++}),this.uuid=cr(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=Bt.DEFAULT_UP.clone();const e=new P,t=new xi,n=new Sn,s=new P(1,1,1);function r(){n.setFromEuler(t,!1)}function a(){t.setFromQuaternion(n,void 0,!1)}t._onChange(r),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:s},modelViewMatrix:{value:new He},normalMatrix:{value:new Xe}}),this.matrix=new He,this.matrixWorld=new He,this.matrixAutoUpdate=Bt.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=Bt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new zl,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return qi.setFromAxisAngle(e,t),this.quaternion.multiply(qi),this}rotateOnWorldAxis(e,t){return qi.setFromAxisAngle(e,t),this.quaternion.premultiply(qi),this}rotateX(e){return this.rotateOnAxis(Lc,e)}rotateY(e){return this.rotateOnAxis(Dc,e)}rotateZ(e){return this.rotateOnAxis(Ic,e)}translateOnAxis(e,t){return Pc.copy(e).applyQuaternion(this.quaternion),this.position.add(Pc.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(Lc,e)}translateY(e){return this.translateOnAxis(Dc,e)}translateZ(e){return this.translateOnAxis(Ic,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(kn.copy(this.matrixWorld).invert())}lookAt(e,t,n){e.isVector3?_r.copy(e):_r.set(e,t,n);const s=this.parent;this.updateWorldMatrix(!0,!1),Fs.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?kn.lookAt(Fs,_r,this.up):kn.lookAt(_r,Fs,this.up),this.quaternion.setFromRotationMatrix(kn),s&&(kn.extractRotation(s.matrixWorld),qi.setFromRotationMatrix(kn),this.quaternion.premultiply(qi.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(st("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(Nc),Yi.child=e,this.dispatchEvent(Yi),Yi.child=null):st("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}const t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(Wf),Fa.child=e,this.dispatchEvent(Fa),Fa.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),kn.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),kn.multiply(e.parent.matrixWorld)),e.applyMatrix4(kn),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(Nc),Yi.child=e,this.dispatchEvent(Yi),Yi.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let n=0,s=this.children.length;n<s;n++){const a=this.children[n].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,n=[]){this[e]===t&&n.push(this);const s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].getObjectsByProperty(e,t,n);return n}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Fs,e,Vf),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Fs,Gf,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);const t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverseVisible(e)}traverseAncestors(e){const t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);const e=this.pivot;if(e!==null){const t=e.x,n=e.y,s=e.z,r=this.matrix.elements;r[12]+=t-r[0]*t-r[4]*n-r[8]*s,r[13]+=n-r[1]*t-r[5]*n-r[9]*s,r[14]+=s-r[2]*t-r[6]*n-r[10]*s}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].updateMatrixWorld(e)}updateWorldMatrix(e,t,n=!1){const s=this.parent;if(e===!0&&s!==null&&s.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||n)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,n=!0),t===!0){const r=this.children;for(let a=0,o=r.length;a<o;a++)r[a].updateWorldMatrix(!1,!0,n)}}toJSON(e){const t=e===void 0||typeof e=="string",n={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const s={};s.uuid=this.uuid,s.type=this.type,this.name!==""&&(s.name=this.name),this.castShadow===!0&&(s.castShadow=!0),this.receiveShadow===!0&&(s.receiveShadow=!0),this.visible===!1&&(s.visible=!1),this.frustumCulled===!1&&(s.frustumCulled=!1),this.renderOrder!==0&&(s.renderOrder=this.renderOrder),this.static!==!1&&(s.static=this.static),Object.keys(this.userData).length>0&&(s.userData=this.userData),s.layers=this.layers.mask,s.matrix=this.matrix.toArray(),s.up=this.up.toArray(),this.pivot!==null&&(s.pivot=this.pivot.toArray()),this.matrixAutoUpdate===!1&&(s.matrixAutoUpdate=!1),this.morphTargetDictionary!==void 0&&(s.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(s.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(s.type="InstancedMesh",s.count=this.count,s.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(s.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(s.type="BatchedMesh",s.perObjectFrustumCulled=this.perObjectFrustumCulled,s.sortObjects=this.sortObjects,s.drawRanges=this._drawRanges,s.reservedRanges=this._reservedRanges,s.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),s.instanceInfo=this._instanceInfo.map(o=>({...o})),s.availableInstanceIds=this._availableInstanceIds.slice(),s.availableGeometryIds=this._availableGeometryIds.slice(),s.nextIndexStart=this._nextIndexStart,s.nextVertexStart=this._nextVertexStart,s.geometryCount=this._geometryCount,s.maxInstanceCount=this._maxInstanceCount,s.maxVertexCount=this._maxVertexCount,s.maxIndexCount=this._maxIndexCount,s.geometryInitialized=this._geometryInitialized,s.matricesTexture=this._matricesTexture.toJSON(e),s.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(s.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(s.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(s.boundingBox=this.boundingBox.toJSON()));function r(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?s.background=this.background.toJSON():this.background.isTexture&&(s.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(s.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){s.geometry=r(e.geometries,this.geometry);const o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){const l=o.shapes;if(Array.isArray(l))for(let c=0,h=l.length;c<h;c++){const d=l[c];r(e.shapes,d)}else r(e.shapes,l)}}if(this.isSkinnedMesh&&(s.bindMode=this.bindMode,s.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(r(e.skeletons,this.skeleton),s.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(r(e.materials,this.material[l]));s.material=o}else s.material=r(e.materials,this.material);if(this.children.length>0){s.children=[];for(let o=0;o<this.children.length;o++)s.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){s.animations=[];for(let o=0;o<this.animations.length;o++){const l=this.animations[o];s.animations.push(r(e.animations,l))}}if(t){const o=a(e.geometries),l=a(e.materials),c=a(e.textures),h=a(e.images),d=a(e.shapes),u=a(e.skeletons),p=a(e.animations),g=a(e.nodes);o.length>0&&(n.geometries=o),l.length>0&&(n.materials=l),c.length>0&&(n.textures=c),h.length>0&&(n.images=h),d.length>0&&(n.shapes=d),u.length>0&&(n.skeletons=u),p.length>0&&(n.animations=p),g.length>0&&(n.nodes=g)}return n.object=s,n;function a(o){const l=[];for(const c in o){const h=o[c];delete h.metadata,l.push(h)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let n=0;n<e.children.length;n++){const s=e.children[n];this.add(s.clone())}return this}}Bt.DEFAULT_UP=new P(0,1,0);Bt.DEFAULT_MATRIX_AUTO_UPDATE=!0;Bt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class wt extends Bt{constructor(){super(),this.isGroup=!0,this.type="Group"}}const $f={type:"move"};class ka{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new wt,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new wt,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new P,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new P),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new wt,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new P,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new P,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const t=this._hand;if(t)for(const n of e.hand.values())this._getHandJoint(t,n)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,n){let s=null,r=null,a=null;const o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(const x of e.hand.values()){const m=t.getJointPose(x,n),f=this._getHandJoint(c,x);m!==null&&(f.matrix.fromArray(m.transform.matrix),f.matrix.decompose(f.position,f.rotation,f.scale),f.matrixWorldNeedsUpdate=!0,f.jointRadius=m.radius),f.visible=m!==null}const h=c.joints["index-finger-tip"],d=c.joints["thumb-tip"],u=h.position.distanceTo(d.position),p=.02,g=.005;c.inputState.pinching&&u>p+g?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&u<=p-g&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(r=t.getPose(e.gripSpace,n),r!==null&&(l.matrix.fromArray(r.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,r.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(r.linearVelocity)):l.hasLinearVelocity=!1,r.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(r.angularVelocity)):l.hasAngularVelocity=!1,l.eventsEnabled&&l.dispatchEvent({type:"gripUpdated",data:e,target:this})));o!==null&&(s=t.getPose(e.targetRaySpace,n),s===null&&r!==null&&(s=r),s!==null&&(o.matrix.fromArray(s.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,s.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(s.linearVelocity)):o.hasLinearVelocity=!1,s.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(s.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent($f)))}return o!==null&&(o.visible=s!==null),l!==null&&(l.visible=r!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){const n=new wt;n.matrixAutoUpdate=!1,n.visible=!1,e.joints[t.jointName]=n,e.add(n)}return e.joints[t.jointName]}}const $u={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},si={h:0,s:0,l:0},vr={h:0,s:0,l:0};function Ba(i,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?i+(e-i)*6*t:t<1/2?e:t<2/3?i+(e-i)*6*(2/3-t):i}class ye{constructor(e,t,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,n)}set(e,t,n){if(t===void 0&&n===void 0){const s=e;s&&s.isColor?this.copy(s):typeof s=="number"?this.setHex(s):typeof s=="string"&&this.setStyle(s)}else this.setRGB(e,t,n);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=sn){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,et.colorSpaceToWorking(this,t),this}setRGB(e,t,n,s=et.workingColorSpace){return this.r=e,this.g=t,this.b=n,et.colorSpaceToWorking(this,s),this}setHSL(e,t,n,s=et.workingColorSpace){if(e=Lf(e,1),t=Qe(t,0,1),n=Qe(n,0,1),t===0)this.r=this.g=this.b=n;else{const r=n<=.5?n*(1+t):n+t-n*t,a=2*n-r;this.r=Ba(a,r,e+1/3),this.g=Ba(a,r,e),this.b=Ba(a,r,e-1/3)}return et.colorSpaceToWorking(this,s),this}setStyle(e,t=sn){function n(r){r!==void 0&&parseFloat(r)<1&&ke("Color: Alpha component of "+e+" will be ignored.")}let s;if(s=/^(\w+)\(([^\)]*)\)/.exec(e)){let r;const a=s[1],o=s[2];switch(a){case"rgb":case"rgba":if(r=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(255,parseInt(r[1],10))/255,Math.min(255,parseInt(r[2],10))/255,Math.min(255,parseInt(r[3],10))/255,t);if(r=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(100,parseInt(r[1],10))/100,Math.min(100,parseInt(r[2],10))/100,Math.min(100,parseInt(r[3],10))/100,t);break;case"hsl":case"hsla":if(r=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setHSL(parseFloat(r[1])/360,parseFloat(r[2])/100,parseFloat(r[3])/100,t);break;default:ke("Color: Unknown color model "+e)}}else if(s=/^\#([A-Fa-f\d]+)$/.exec(e)){const r=s[1],a=r.length;if(a===3)return this.setRGB(parseInt(r.charAt(0),16)/15,parseInt(r.charAt(1),16)/15,parseInt(r.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(r,16),t);ke("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=sn){const n=$u[e.toLowerCase()];return n!==void 0?this.setHex(n,t):ke("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Zn(e.r),this.g=Zn(e.g),this.b=Zn(e.b),this}copyLinearToSRGB(e){return this.r=_s(e.r),this.g=_s(e.g),this.b=_s(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=sn){return et.workingToColorSpace(Yt.copy(this),e),Math.round(Qe(Yt.r*255,0,255))*65536+Math.round(Qe(Yt.g*255,0,255))*256+Math.round(Qe(Yt.b*255,0,255))}getHexString(e=sn){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=et.workingColorSpace){et.workingToColorSpace(Yt.copy(this),t);const n=Yt.r,s=Yt.g,r=Yt.b,a=Math.max(n,s,r),o=Math.min(n,s,r);let l,c;const h=(o+a)/2;if(o===a)l=0,c=0;else{const d=a-o;switch(c=h<=.5?d/(a+o):d/(2-a-o),a){case n:l=(s-r)/d+(s<r?6:0);break;case s:l=(r-n)/d+2;break;case r:l=(n-s)/d+4;break}l/=6}return e.h=l,e.s=c,e.l=h,e}getRGB(e,t=et.workingColorSpace){return et.workingToColorSpace(Yt.copy(this),t),e.r=Yt.r,e.g=Yt.g,e.b=Yt.b,e}getStyle(e=sn){et.workingToColorSpace(Yt.copy(this),e);const t=Yt.r,n=Yt.g,s=Yt.b;return e!==sn?`color(${e} ${t.toFixed(3)} ${n.toFixed(3)} ${s.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(n*255)},${Math.round(s*255)})`}offsetHSL(e,t,n){return this.getHSL(si),this.setHSL(si.h+e,si.s+t,si.l+n)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,n){return this.r=e.r+(t.r-e.r)*n,this.g=e.g+(t.g-e.g)*n,this.b=e.b+(t.b-e.b)*n,this}lerpHSL(e,t){this.getHSL(si),e.getHSL(vr);const n=Da(si.h,vr.h,t),s=Da(si.s,vr.s,t),r=Da(si.l,vr.l,t);return this.setHSL(n,s,r),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const t=this.r,n=this.g,s=this.b,r=e.elements;return this.r=r[0]*t+r[3]*n+r[6]*s,this.g=r[1]*t+r[4]*n+r[7]*s,this.b=r[2]*t+r[5]*n+r[8]*s,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const Yt=new ye;ye.NAMES=$u;class Xf extends Bt{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new xi,this.environmentIntensity=1,this.environmentRotation=new xi,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}}const xn=new P,Bn=new P,za=new P,zn=new P,Zi=new P,Ki=new P,Uc=new P,Ha=new P,Va=new P,Ga=new P,Wa=new At,$a=new At,Xa=new At;class mn{constructor(e=new P,t=new P,n=new P){this.a=e,this.b=t,this.c=n}static getNormal(e,t,n,s){s.subVectors(n,t),xn.subVectors(e,t),s.cross(xn);const r=s.lengthSq();return r>0?s.multiplyScalar(1/Math.sqrt(r)):s.set(0,0,0)}static getBarycoord(e,t,n,s,r){xn.subVectors(s,t),Bn.subVectors(n,t),za.subVectors(e,t);const a=xn.dot(xn),o=xn.dot(Bn),l=xn.dot(za),c=Bn.dot(Bn),h=Bn.dot(za),d=a*c-o*o;if(d===0)return r.set(0,0,0),null;const u=1/d,p=(c*l-o*h)*u,g=(a*h-o*l)*u;return r.set(1-p-g,g,p)}static containsPoint(e,t,n,s){return this.getBarycoord(e,t,n,s,zn)===null?!1:zn.x>=0&&zn.y>=0&&zn.x+zn.y<=1}static getInterpolation(e,t,n,s,r,a,o,l){return this.getBarycoord(e,t,n,s,zn)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(r,zn.x),l.addScaledVector(a,zn.y),l.addScaledVector(o,zn.z),l)}static getInterpolatedAttribute(e,t,n,s,r,a){return Wa.setScalar(0),$a.setScalar(0),Xa.setScalar(0),Wa.fromBufferAttribute(e,t),$a.fromBufferAttribute(e,n),Xa.fromBufferAttribute(e,s),a.setScalar(0),a.addScaledVector(Wa,r.x),a.addScaledVector($a,r.y),a.addScaledVector(Xa,r.z),a}static isFrontFacing(e,t,n,s){return xn.subVectors(n,t),Bn.subVectors(e,t),xn.cross(Bn).dot(s)<0}set(e,t,n){return this.a.copy(e),this.b.copy(t),this.c.copy(n),this}setFromPointsAndIndices(e,t,n,s){return this.a.copy(e[t]),this.b.copy(e[n]),this.c.copy(e[s]),this}setFromAttributeAndIndices(e,t,n,s){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,n),this.c.fromBufferAttribute(e,s),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return xn.subVectors(this.c,this.b),Bn.subVectors(this.a,this.b),xn.cross(Bn).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return mn.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return mn.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,n,s,r){return mn.getInterpolation(e,this.a,this.b,this.c,t,n,s,r)}containsPoint(e){return mn.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return mn.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){const n=this.a,s=this.b,r=this.c;let a,o;Zi.subVectors(s,n),Ki.subVectors(r,n),Ha.subVectors(e,n);const l=Zi.dot(Ha),c=Ki.dot(Ha);if(l<=0&&c<=0)return t.copy(n);Va.subVectors(e,s);const h=Zi.dot(Va),d=Ki.dot(Va);if(h>=0&&d<=h)return t.copy(s);const u=l*d-h*c;if(u<=0&&l>=0&&h<=0)return a=l/(l-h),t.copy(n).addScaledVector(Zi,a);Ga.subVectors(e,r);const p=Zi.dot(Ga),g=Ki.dot(Ga);if(g>=0&&p<=g)return t.copy(r);const x=p*c-l*g;if(x<=0&&c>=0&&g<=0)return o=c/(c-g),t.copy(n).addScaledVector(Ki,o);const m=h*g-p*d;if(m<=0&&d-h>=0&&p-g>=0)return Uc.subVectors(r,s),o=(d-h)/(d-h+(p-g)),t.copy(s).addScaledVector(Uc,o);const f=1/(m+x+u);return a=x*f,o=u*f,t.copy(n).addScaledVector(Zi,a).addScaledVector(Ki,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class zi{constructor(e=new P(1/0,1/0,1/0),t=new P(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t+=3)this.expandByPoint(yn.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,n=e.count;t<n;t++)this.expandByPoint(yn.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){const n=yn.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(n),this.max.copy(e).add(n),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);const n=e.geometry;if(n!==void 0){const r=n.getAttribute("position");if(t===!0&&r!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=r.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,yn):yn.fromBufferAttribute(r,a),yn.applyMatrix4(e.matrixWorld),this.expandByPoint(yn);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),xr.copy(e.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),xr.copy(n.boundingBox)),xr.applyMatrix4(e.matrixWorld),this.union(xr)}const s=e.children;for(let r=0,a=s.length;r<a;r++)this.expandByObject(s[r],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,yn),yn.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,n;return e.normal.x>0?(t=e.normal.x*this.min.x,n=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,n=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,n+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,n+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,n+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,n+=e.normal.z*this.min.z),t<=-e.constant&&n>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(ks),yr.subVectors(this.max,ks),ji.subVectors(e.a,ks),Ji.subVectors(e.b,ks),Qi.subVectors(e.c,ks),ri.subVectors(Ji,ji),ai.subVectors(Qi,Ji),Ai.subVectors(ji,Qi);let t=[0,-ri.z,ri.y,0,-ai.z,ai.y,0,-Ai.z,Ai.y,ri.z,0,-ri.x,ai.z,0,-ai.x,Ai.z,0,-Ai.x,-ri.y,ri.x,0,-ai.y,ai.x,0,-Ai.y,Ai.x,0];return!qa(t,ji,Ji,Qi,yr)||(t=[1,0,0,0,1,0,0,0,1],!qa(t,ji,Ji,Qi,yr))?!1:(br.crossVectors(ri,ai),t=[br.x,br.y,br.z],qa(t,ji,Ji,Qi,yr))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,yn).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(yn).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(Hn[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),Hn[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),Hn[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),Hn[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),Hn[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),Hn[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),Hn[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),Hn[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(Hn),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const Hn=[new P,new P,new P,new P,new P,new P,new P,new P],yn=new P,xr=new zi,ji=new P,Ji=new P,Qi=new P,ri=new P,ai=new P,Ai=new P,ks=new P,yr=new P,br=new P,Ri=new P;function qa(i,e,t,n,s){for(let r=0,a=i.length-3;r<=a;r+=3){Ri.fromArray(i,r);const o=s.x*Math.abs(Ri.x)+s.y*Math.abs(Ri.y)+s.z*Math.abs(Ri.z),l=e.dot(Ri),c=t.dot(Ri),h=n.dot(Ri);if(Math.max(-Math.max(l,c,h),Math.min(l,c,h))>o)return!1}return!0}const Ut=new P,Mr=new Fe;let qf=0;class Mn extends Ei{constructor(e,t,n=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:qf++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=n,this.usage=bc,this.updateRanges=[],this.gpuType=bn,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,n){e*=this.itemSize,n*=t.itemSize;for(let s=0,r=this.itemSize;s<r;s++)this.array[e+s]=t.array[n+s];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,n=this.count;t<n;t++)Mr.fromBufferAttribute(this,t),Mr.applyMatrix3(e),this.setXY(t,Mr.x,Mr.y);else if(this.itemSize===3)for(let t=0,n=this.count;t<n;t++)Ut.fromBufferAttribute(this,t),Ut.applyMatrix3(e),this.setXYZ(t,Ut.x,Ut.y,Ut.z);return this}applyMatrix4(e){for(let t=0,n=this.count;t<n;t++)Ut.fromBufferAttribute(this,t),Ut.applyMatrix4(e),this.setXYZ(t,Ut.x,Ut.y,Ut.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)Ut.fromBufferAttribute(this,t),Ut.applyNormalMatrix(e),this.setXYZ(t,Ut.x,Ut.y,Ut.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)Ut.fromBufferAttribute(this,t),Ut.transformDirection(e),this.setXYZ(t,Ut.x,Ut.y,Ut.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let n=this.array[e*this.itemSize+t];return this.normalized&&(n=Os(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=tn(n,this.array)),this.array[e*this.itemSize+t]=n,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=Os(t,this.array)),t}setX(e,t){return this.normalized&&(t=tn(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=Os(t,this.array)),t}setY(e,t){return this.normalized&&(t=tn(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=Os(t,this.array)),t}setZ(e,t){return this.normalized&&(t=tn(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=Os(t,this.array)),t}setW(e,t){return this.normalized&&(t=tn(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,n){return e*=this.itemSize,this.normalized&&(t=tn(t,this.array),n=tn(n,this.array)),this.array[e+0]=t,this.array[e+1]=n,this}setXYZ(e,t,n,s){return e*=this.itemSize,this.normalized&&(t=tn(t,this.array),n=tn(n,this.array),s=tn(s,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this}setXYZW(e,t,n,s,r){return e*=this.itemSize,this.normalized&&(t=tn(t,this.array),n=tn(n,this.array),s=tn(s,this.array),r=tn(r,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this.array[e+3]=r,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==bc&&(e.usage=this.usage),e}dispose(){this.dispatchEvent({type:"dispose"})}}class Xu extends Mn{constructor(e,t,n){super(new Uint16Array(e),t,n)}}class qu extends Mn{constructor(e,t,n){super(new Uint32Array(e),t,n)}}class St extends Mn{constructor(e,t,n){super(new Float32Array(e),t,n)}}const Yf=new zi,Bs=new P,Ya=new P;class Ls{constructor(e=new P,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){const n=this.center;t!==void 0?n.copy(t):Yf.setFromPoints(e).getCenter(n);let s=0;for(let r=0,a=e.length;r<a;r++)s=Math.max(s,n.distanceToSquared(e[r]));return this.radius=Math.sqrt(s),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){const n=this.center.distanceToSquared(e);return t.copy(e),n>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;Bs.subVectors(e,this.center);const t=Bs.lengthSq();if(t>this.radius*this.radius){const n=Math.sqrt(t),s=(n-this.radius)*.5;this.center.addScaledVector(Bs,s/n),this.radius+=s}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Ya.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(Bs.copy(e.center).add(Ya)),this.expandByPoint(Bs.copy(e.center).sub(Ya))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}let Zf=0;const fn=new He,Za=new Bt,es=new P,ln=new zi,zs=new zi,Vt=new P;class jt extends Ei{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:Zf++}),this.uuid=cr(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(Af(e)?qu:Xu)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,n=0){this.groups.push({start:e,count:t,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){const t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);const n=this.attributes.normal;if(n!==void 0){const r=new Xe().getNormalMatrix(e);n.applyNormalMatrix(r),n.needsUpdate=!0}const s=this.attributes.tangent;return s!==void 0&&(s.transformDirection(e),s.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(e){return fn.makeRotationFromQuaternion(e),this.applyMatrix4(fn),this}rotateX(e){return fn.makeRotationX(e),this.applyMatrix4(fn),this}rotateY(e){return fn.makeRotationY(e),this.applyMatrix4(fn),this}rotateZ(e){return fn.makeRotationZ(e),this.applyMatrix4(fn),this}translate(e,t,n){return fn.makeTranslation(e,t,n),this.applyMatrix4(fn),this}scale(e,t,n){return fn.makeScale(e,t,n),this.applyMatrix4(fn),this}lookAt(e){return Za.lookAt(e),Za.updateMatrix(),this.applyMatrix4(Za.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(es).negate(),this.translate(es.x,es.y,es.z),this}setFromPoints(e){const t=this.getAttribute("position");if(t===void 0){const n=[];for(let s=0,r=e.length;s<r;s++){const a=e[s];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new St(n,3))}else{const n=Math.min(e.length,t.count);for(let s=0;s<n;s++){const r=e[s];t.setXYZ(s,r.x,r.y,r.z||0)}e.length>t.count&&ke("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new zi);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){st("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new P(-1/0,-1/0,-1/0),new P(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let n=0,s=t.length;n<s;n++){const r=t[n];ln.setFromBufferAttribute(r),this.morphTargetsRelative?(Vt.addVectors(this.boundingBox.min,ln.min),this.boundingBox.expandByPoint(Vt),Vt.addVectors(this.boundingBox.max,ln.max),this.boundingBox.expandByPoint(Vt)):(this.boundingBox.expandByPoint(ln.min),this.boundingBox.expandByPoint(ln.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&st('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Ls);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){st("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new P,1/0);return}if(e){const n=this.boundingSphere.center;if(ln.setFromBufferAttribute(e),t)for(let r=0,a=t.length;r<a;r++){const o=t[r];zs.setFromBufferAttribute(o),this.morphTargetsRelative?(Vt.addVectors(ln.min,zs.min),ln.expandByPoint(Vt),Vt.addVectors(ln.max,zs.max),ln.expandByPoint(Vt)):(ln.expandByPoint(zs.min),ln.expandByPoint(zs.max))}ln.getCenter(n);let s=0;for(let r=0,a=e.count;r<a;r++)Vt.fromBufferAttribute(e,r),s=Math.max(s,n.distanceToSquared(Vt));if(t)for(let r=0,a=t.length;r<a;r++){const o=t[r],l=this.morphTargetsRelative;for(let c=0,h=o.count;c<h;c++)Vt.fromBufferAttribute(o,c),l&&(es.fromBufferAttribute(e,c),Vt.add(es)),s=Math.max(s,n.distanceToSquared(Vt))}this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&st('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){st("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const n=t.position,s=t.normal,r=t.uv;let a=this.getAttribute("tangent");(a===void 0||a.count!==n.count)&&(a=new Mn(new Float32Array(4*n.count),4),this.setAttribute("tangent",a));const o=[],l=[];for(let v=0;v<n.count;v++)o[v]=new P,l[v]=new P;const c=new P,h=new P,d=new P,u=new Fe,p=new Fe,g=new Fe,x=new P,m=new P;function f(v,w,C){c.fromBufferAttribute(n,v),h.fromBufferAttribute(n,w),d.fromBufferAttribute(n,C),u.fromBufferAttribute(r,v),p.fromBufferAttribute(r,w),g.fromBufferAttribute(r,C),h.sub(c),d.sub(c),p.sub(u),g.sub(u);const L=1/(p.x*g.y-g.x*p.y);isFinite(L)&&(x.copy(h).multiplyScalar(g.y).addScaledVector(d,-p.y).multiplyScalar(L),m.copy(d).multiplyScalar(p.x).addScaledVector(h,-g.x).multiplyScalar(L),o[v].add(x),o[w].add(x),o[C].add(x),l[v].add(m),l[w].add(m),l[C].add(m))}let M=this.groups;M.length===0&&(M=[{start:0,count:e.count}]);for(let v=0,w=M.length;v<w;++v){const C=M[v],L=C.start,N=C.count;for(let V=L,$=L+N;V<$;V+=3)f(e.getX(V+0),e.getX(V+1),e.getX(V+2))}const E=new P,y=new P,T=new P,S=new P;function R(v){T.fromBufferAttribute(s,v),S.copy(T);const w=o[v];E.copy(w),E.sub(T.multiplyScalar(T.dot(w))).normalize(),y.crossVectors(S,w);const L=y.dot(l[v])<0?-1:1;a.setXYZW(v,E.x,E.y,E.z,L)}for(let v=0,w=M.length;v<w;++v){const C=M[v],L=C.start,N=C.count;for(let V=L,$=L+N;V<$;V+=3)R(e.getX(V+0)),R(e.getX(V+1)),R(e.getX(V+2))}this._transformed=!0}computeVertexNormals(){const e=this.index,t=this.getAttribute("position");if(t!==void 0){let n=this.getAttribute("normal");if(n===void 0||n.count!==t.count)n=new Mn(new Float32Array(t.count*3),3),this.setAttribute("normal",n);else for(let u=0,p=n.count;u<p;u++)n.setXYZ(u,0,0,0);const s=new P,r=new P,a=new P,o=new P,l=new P,c=new P,h=new P,d=new P;if(e)for(let u=0,p=e.count;u<p;u+=3){const g=e.getX(u+0),x=e.getX(u+1),m=e.getX(u+2);s.fromBufferAttribute(t,g),r.fromBufferAttribute(t,x),a.fromBufferAttribute(t,m),h.subVectors(a,r),d.subVectors(s,r),h.cross(d),o.fromBufferAttribute(n,g),l.fromBufferAttribute(n,x),c.fromBufferAttribute(n,m),o.add(h),l.add(h),c.add(h),n.setXYZ(g,o.x,o.y,o.z),n.setXYZ(x,l.x,l.y,l.z),n.setXYZ(m,c.x,c.y,c.z)}else for(let u=0,p=t.count;u<p;u+=3)s.fromBufferAttribute(t,u+0),r.fromBufferAttribute(t,u+1),a.fromBufferAttribute(t,u+2),h.subVectors(a,r),d.subVectors(s,r),h.cross(d),n.setXYZ(u+0,h.x,h.y,h.z),n.setXYZ(u+1,h.x,h.y,h.z),n.setXYZ(u+2,h.x,h.y,h.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let t=0,n=e.count;t<n;t++)Vt.fromBufferAttribute(e,t),Vt.normalize(),e.setXYZ(t,Vt.x,Vt.y,Vt.z)}toNonIndexed(){function e(o,l){const c=o.array,h=o.itemSize,d=o.normalized,u=new c.constructor(l.length*h);let p=0,g=0;for(let x=0,m=l.length;x<m;x++){o.isInterleavedBufferAttribute?p=l[x]*o.data.stride+o.offset:p=l[x]*h;for(let f=0;f<h;f++)u[g++]=c[p++]}return new Mn(u,h,d)}if(this.index===null)return ke("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const t=new jt,n=this.index.array,s=this.attributes;for(const o in s){const l=s[o],c=e(l,n);t.setAttribute(o,c)}const r=this.morphAttributes;for(const o in r){const l=[],c=r[o];for(let h=0,d=c.length;h<d;h++){const u=c[h],p=e(u,n);l.push(p)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;const a=this.groups;for(let o=0,l=a.length;o<l;o++){const c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){const l=this.parameters;for(const c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};const t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});const n=this.attributes;for(const l in n){const c=n[l];e.data.attributes[l]=c.toJSON(e.data)}const s={};let r=!1;for(const l in this.morphAttributes){const c=this.morphAttributes[l],h=[];for(let d=0,u=c.length;d<u;d++){const p=c[d];h.push(p.toJSON(e.data))}h.length>0&&(s[l]=h,r=!0)}r&&(e.data.morphAttributes=s,e.data.morphTargetsRelative=this.morphTargetsRelative);const a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));const o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const t={};this.name=e.name;const n=e.index;n!==null&&this.setIndex(n.clone());const s=e.attributes;for(const c in s){const h=s[c];this.setAttribute(c,h.clone(t))}const r=e.morphAttributes;for(const c in r){const h=[],d=r[c];for(let u=0,p=d.length;u<p;u++)h.push(d[u].clone(t));this.morphAttributes[c]=h}this.morphTargetsRelative=e.morphTargetsRelative;const a=e.groups;for(let c=0,h=a.length;c<h;c++){const d=a[c];this.addGroup(d.start,d.count,d.materialIndex)}const o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());const l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this._transformed=e._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}}let Kf=0;class Ds extends Ei{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Kf++}),this.uuid=cr(),this.name="",this.type="Material",this.blending=ms,this.side=vi,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=wo,this.blendDst=To,this.blendEquation=Ii,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new ye(0,0,0),this.blendAlpha=0,this.depthFunc=ys,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=yc,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Wi,this.stencilZFail=Wi,this.stencilZPass=Wi,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const t in e){const n=e[t];if(n===void 0){ke(`Material: parameter '${t}' has value of undefined.`);continue}const s=this[t];if(s===void 0){ke(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}s&&s.isColor?s.set(n):s&&s.isVector2&&n&&n.isVector2||s&&s.isEuler&&n&&n.isEuler||s&&s.isVector3&&n&&n.isVector3?s.copy(n):this[t]=n}}toJSON(e){const t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});const n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,this.name!==""&&(n.name=this.name),this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(e).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(e).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(e).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(e).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(e).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.shadowSide!==null&&(n.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),this.blending!==ms&&(n.blending=this.blending),this.side!==vi&&(n.side=this.side),this.vertexColors===!0&&(n.vertexColors=!0),this.opacity<1&&(n.opacity=this.opacity),this.transparent===!0&&(n.transparent=!0),this.blendSrc!==wo&&(n.blendSrc=this.blendSrc),this.blendDst!==To&&(n.blendDst=this.blendDst),this.blendEquation!==Ii&&(n.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(n.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(n.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(n.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(n.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(n.blendAlpha=this.blendAlpha),this.depthFunc!==ys&&(n.depthFunc=this.depthFunc),this.depthTest===!1&&(n.depthTest=this.depthTest),this.depthWrite===!1&&(n.depthWrite=this.depthWrite),this.colorWrite===!1&&(n.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(n.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==yc&&(n.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(n.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(n.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==Wi&&(n.stencilFail=this.stencilFail),this.stencilZFail!==Wi&&(n.stencilZFail=this.stencilZFail),this.stencilZPass!==Wi&&(n.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(n.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(n.rotation=this.rotation),this.polygonOffset===!0&&(n.polygonOffset=!0),this.polygonOffsetFactor!==0&&(n.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(n.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(n.linewidth=this.linewidth),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.dithering===!0&&(n.dithering=!0),this.alphaTest>0&&(n.alphaTest=this.alphaTest),this.alphaHash===!0&&(n.alphaHash=!0),this.alphaToCoverage===!0&&(n.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(n.premultipliedAlpha=!0),this.forceSinglePass===!0&&(n.forceSinglePass=!0),this.allowOverride===!1&&(n.allowOverride=!1),this.wireframe===!0&&(n.wireframe=!0),this.wireframeLinewidth>1&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(n.flatShading=!0),this.visible===!1&&(n.visible=!1),this.toneMapped===!1&&(n.toneMapped=!1),this.fog===!1&&(n.fog=!1),Object.keys(this.userData).length>0&&(n.userData=this.userData);function s(r){const a=[];for(const o in r){const l=r[o];delete l.metadata,a.push(l)}return a}if(t){const r=s(e.textures),a=s(e.images);r.length>0&&(n.textures=r),a.length>0&&(n.images=a)}return n}fromJSON(e,t){if(e.uuid!==void 0&&(this.uuid=e.uuid),e.name!==void 0&&(this.name=e.name),e.color!==void 0&&this.color!==void 0&&this.color.setHex(e.color),e.roughness!==void 0&&(this.roughness=e.roughness),e.metalness!==void 0&&(this.metalness=e.metalness),e.sheen!==void 0&&(this.sheen=e.sheen),e.sheenColor!==void 0&&(this.sheenColor=new ye().setHex(e.sheenColor)),e.sheenRoughness!==void 0&&(this.sheenRoughness=e.sheenRoughness),e.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(e.emissive),e.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(e.specular),e.specularIntensity!==void 0&&(this.specularIntensity=e.specularIntensity),e.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(e.specularColor),e.shininess!==void 0&&(this.shininess=e.shininess),e.clearcoat!==void 0&&(this.clearcoat=e.clearcoat),e.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=e.clearcoatRoughness),e.dispersion!==void 0&&(this.dispersion=e.dispersion),e.iridescence!==void 0&&(this.iridescence=e.iridescence),e.iridescenceIOR!==void 0&&(this.iridescenceIOR=e.iridescenceIOR),e.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=e.iridescenceThicknessRange),e.transmission!==void 0&&(this.transmission=e.transmission),e.thickness!==void 0&&(this.thickness=e.thickness),e.attenuationDistance!==void 0&&(this.attenuationDistance=e.attenuationDistance),e.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(e.attenuationColor),e.anisotropy!==void 0&&(this.anisotropy=e.anisotropy),e.anisotropyRotation!==void 0&&(this.anisotropyRotation=e.anisotropyRotation),e.fog!==void 0&&(this.fog=e.fog),e.flatShading!==void 0&&(this.flatShading=e.flatShading),e.blending!==void 0&&(this.blending=e.blending),e.combine!==void 0&&(this.combine=e.combine),e.side!==void 0&&(this.side=e.side),e.shadowSide!==void 0&&(this.shadowSide=e.shadowSide),e.opacity!==void 0&&(this.opacity=e.opacity),e.transparent!==void 0&&(this.transparent=e.transparent),e.alphaTest!==void 0&&(this.alphaTest=e.alphaTest),e.alphaHash!==void 0&&(this.alphaHash=e.alphaHash),e.depthFunc!==void 0&&(this.depthFunc=e.depthFunc),e.depthTest!==void 0&&(this.depthTest=e.depthTest),e.depthWrite!==void 0&&(this.depthWrite=e.depthWrite),e.colorWrite!==void 0&&(this.colorWrite=e.colorWrite),e.blendSrc!==void 0&&(this.blendSrc=e.blendSrc),e.blendDst!==void 0&&(this.blendDst=e.blendDst),e.blendEquation!==void 0&&(this.blendEquation=e.blendEquation),e.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=e.blendSrcAlpha),e.blendDstAlpha!==void 0&&(this.blendDstAlpha=e.blendDstAlpha),e.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=e.blendEquationAlpha),e.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(e.blendColor),e.blendAlpha!==void 0&&(this.blendAlpha=e.blendAlpha),e.stencilWriteMask!==void 0&&(this.stencilWriteMask=e.stencilWriteMask),e.stencilFunc!==void 0&&(this.stencilFunc=e.stencilFunc),e.stencilRef!==void 0&&(this.stencilRef=e.stencilRef),e.stencilFuncMask!==void 0&&(this.stencilFuncMask=e.stencilFuncMask),e.stencilFail!==void 0&&(this.stencilFail=e.stencilFail),e.stencilZFail!==void 0&&(this.stencilZFail=e.stencilZFail),e.stencilZPass!==void 0&&(this.stencilZPass=e.stencilZPass),e.stencilWrite!==void 0&&(this.stencilWrite=e.stencilWrite),e.wireframe!==void 0&&(this.wireframe=e.wireframe),e.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=e.wireframeLinewidth),e.wireframeLinecap!==void 0&&(this.wireframeLinecap=e.wireframeLinecap),e.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=e.wireframeLinejoin),e.rotation!==void 0&&(this.rotation=e.rotation),e.linewidth!==void 0&&(this.linewidth=e.linewidth),e.dashSize!==void 0&&(this.dashSize=e.dashSize),e.gapSize!==void 0&&(this.gapSize=e.gapSize),e.scale!==void 0&&(this.scale=e.scale),e.polygonOffset!==void 0&&(this.polygonOffset=e.polygonOffset),e.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=e.polygonOffsetFactor),e.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=e.polygonOffsetUnits),e.dithering!==void 0&&(this.dithering=e.dithering),e.alphaToCoverage!==void 0&&(this.alphaToCoverage=e.alphaToCoverage),e.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=e.premultipliedAlpha),e.forceSinglePass!==void 0&&(this.forceSinglePass=e.forceSinglePass),e.allowOverride!==void 0&&(this.allowOverride=e.allowOverride),e.visible!==void 0&&(this.visible=e.visible),e.toneMapped!==void 0&&(this.toneMapped=e.toneMapped),e.userData!==void 0&&(this.userData=e.userData),e.vertexColors!==void 0&&(typeof e.vertexColors=="number"?this.vertexColors=e.vertexColors>0:this.vertexColors=e.vertexColors),e.size!==void 0&&(this.size=e.size),e.sizeAttenuation!==void 0&&(this.sizeAttenuation=e.sizeAttenuation),e.map!==void 0&&(this.map=t[e.map]||null),e.matcap!==void 0&&(this.matcap=t[e.matcap]||null),e.alphaMap!==void 0&&(this.alphaMap=t[e.alphaMap]||null),e.bumpMap!==void 0&&(this.bumpMap=t[e.bumpMap]||null),e.bumpScale!==void 0&&(this.bumpScale=e.bumpScale),e.normalMap!==void 0&&(this.normalMap=t[e.normalMap]||null),e.normalMapType!==void 0&&(this.normalMapType=e.normalMapType),e.normalScale!==void 0){let n=e.normalScale;Array.isArray(n)===!1&&(n=[n,n]),this.normalScale=new Fe().fromArray(n)}return e.displacementMap!==void 0&&(this.displacementMap=t[e.displacementMap]||null),e.displacementScale!==void 0&&(this.displacementScale=e.displacementScale),e.displacementBias!==void 0&&(this.displacementBias=e.displacementBias),e.roughnessMap!==void 0&&(this.roughnessMap=t[e.roughnessMap]||null),e.metalnessMap!==void 0&&(this.metalnessMap=t[e.metalnessMap]||null),e.emissiveMap!==void 0&&(this.emissiveMap=t[e.emissiveMap]||null),e.emissiveIntensity!==void 0&&(this.emissiveIntensity=e.emissiveIntensity),e.specularMap!==void 0&&(this.specularMap=t[e.specularMap]||null),e.specularIntensityMap!==void 0&&(this.specularIntensityMap=t[e.specularIntensityMap]||null),e.specularColorMap!==void 0&&(this.specularColorMap=t[e.specularColorMap]||null),e.envMap!==void 0&&(this.envMap=t[e.envMap]||null),e.envMapRotation!==void 0&&this.envMapRotation.fromArray(e.envMapRotation),e.envMapIntensity!==void 0&&(this.envMapIntensity=e.envMapIntensity),e.reflectivity!==void 0&&(this.reflectivity=e.reflectivity),e.refractionRatio!==void 0&&(this.refractionRatio=e.refractionRatio),e.lightMap!==void 0&&(this.lightMap=t[e.lightMap]||null),e.lightMapIntensity!==void 0&&(this.lightMapIntensity=e.lightMapIntensity),e.aoMap!==void 0&&(this.aoMap=t[e.aoMap]||null),e.aoMapIntensity!==void 0&&(this.aoMapIntensity=e.aoMapIntensity),e.gradientMap!==void 0&&(this.gradientMap=t[e.gradientMap]||null),e.clearcoatMap!==void 0&&(this.clearcoatMap=t[e.clearcoatMap]||null),e.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=t[e.clearcoatRoughnessMap]||null),e.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=t[e.clearcoatNormalMap]||null),e.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new Fe().fromArray(e.clearcoatNormalScale)),e.iridescenceMap!==void 0&&(this.iridescenceMap=t[e.iridescenceMap]||null),e.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=t[e.iridescenceThicknessMap]||null),e.transmissionMap!==void 0&&(this.transmissionMap=t[e.transmissionMap]||null),e.thicknessMap!==void 0&&(this.thicknessMap=t[e.thicknessMap]||null),e.anisotropyMap!==void 0&&(this.anisotropyMap=t[e.anisotropyMap]||null),e.sheenColorMap!==void 0&&(this.sheenColorMap=t[e.sheenColorMap]||null),e.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=t[e.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const t=e.clippingPlanes;let n=null;if(t!==null){const s=t.length;n=new Array(s);for(let r=0;r!==s;++r)n[r]=t[r].clone()}return this.clippingPlanes=n,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}const Vn=new P,Ka=new P,Sr=new P,oi=new P,ja=new P,Er=new P,Ja=new P;class Ma{constructor(e=new P,t=new P(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,Vn)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);const n=t.dot(this.direction);return n<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const t=Vn.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(Vn.copy(this.origin).addScaledVector(this.direction,t),Vn.distanceToSquared(e))}distanceSqToSegment(e,t,n,s){Ka.copy(e).add(t).multiplyScalar(.5),Sr.copy(t).sub(e).normalize(),oi.copy(this.origin).sub(Ka);const r=e.distanceTo(t)*.5,a=-this.direction.dot(Sr),o=oi.dot(this.direction),l=-oi.dot(Sr),c=oi.lengthSq(),h=Math.abs(1-a*a);let d,u,p,g;if(h>0)if(d=a*l-o,u=a*o-l,g=r*h,d>=0)if(u>=-g)if(u<=g){const x=1/h;d*=x,u*=x,p=d*(d+a*u+2*o)+u*(a*d+u+2*l)+c}else u=r,d=Math.max(0,-(a*u+o)),p=-d*d+u*(u+2*l)+c;else u=-r,d=Math.max(0,-(a*u+o)),p=-d*d+u*(u+2*l)+c;else u<=-g?(d=Math.max(0,-(-a*r+o)),u=d>0?-r:Math.min(Math.max(-r,-l),r),p=-d*d+u*(u+2*l)+c):u<=g?(d=0,u=Math.min(Math.max(-r,-l),r),p=u*(u+2*l)+c):(d=Math.max(0,-(a*r+o)),u=d>0?r:Math.min(Math.max(-r,-l),r),p=-d*d+u*(u+2*l)+c);else u=a>0?-r:r,d=Math.max(0,-(a*u+o)),p=-d*d+u*(u+2*l)+c;return n&&n.copy(this.origin).addScaledVector(this.direction,d),s&&s.copy(Ka).addScaledVector(Sr,u),p}intersectSphere(e,t){Vn.subVectors(e.center,this.origin);const n=Vn.dot(this.direction),s=Vn.dot(Vn)-n*n,r=e.radius*e.radius;if(s>r)return null;const a=Math.sqrt(r-s),o=n-a,l=n+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;const n=-(this.origin.dot(e.normal)+e.constant)/t;return n>=0?n:null}intersectPlane(e,t){const n=this.distanceToPlane(e);return n===null?null:this.at(n,t)}intersectsPlane(e){const t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let n,s,r,a,o,l;const c=1/this.direction.x,h=1/this.direction.y,d=1/this.direction.z,u=this.origin;return c>=0?(n=(e.min.x-u.x)*c,s=(e.max.x-u.x)*c):(n=(e.max.x-u.x)*c,s=(e.min.x-u.x)*c),h>=0?(r=(e.min.y-u.y)*h,a=(e.max.y-u.y)*h):(r=(e.max.y-u.y)*h,a=(e.min.y-u.y)*h),n>a||r>s||((r>n||isNaN(n))&&(n=r),(a<s||isNaN(s))&&(s=a),d>=0?(o=(e.min.z-u.z)*d,l=(e.max.z-u.z)*d):(o=(e.max.z-u.z)*d,l=(e.min.z-u.z)*d),n>l||o>s)||((o>n||n!==n)&&(n=o),(l<s||s!==s)&&(s=l),s<0)?null:this.at(n>=0?n:s,t)}intersectsBox(e){return this.intersectBox(e,Vn)!==null}intersectTriangle(e,t,n,s,r){ja.subVectors(t,e),Er.subVectors(n,e),Ja.crossVectors(ja,Er);let a=this.direction.dot(Ja),o;if(a>0){if(s)return null;o=1}else if(a<0)o=-1,a=-a;else return null;oi.subVectors(this.origin,e);const l=o*this.direction.dot(Er.crossVectors(oi,Er));if(l<0)return null;const c=o*this.direction.dot(ja.cross(oi));if(c<0||l+c>a)return null;const h=-o*oi.dot(Ja);return h<0?null:this.at(h/a,r)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class ct extends Ds{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new ye(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new xi,this.combine=Pl,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const Oc=new He,Ci=new Ma,wr=new Ls,Fc=new P,Tr=new P,Ar=new P,Rr=new P,Qa=new P,Cr=new P,kc=new P,Pr=new P;class ht extends Bt{constructor(e=new jt,t=new ct){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){const s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){const o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}getVertexPosition(e,t){const n=this.geometry,s=n.attributes.position,r=n.morphAttributes.position,a=n.morphTargetsRelative;t.fromBufferAttribute(s,e);const o=this.morphTargetInfluences;if(r&&o){Cr.set(0,0,0);for(let l=0,c=r.length;l<c;l++){const h=o[l],d=r[l];h!==0&&(Qa.fromBufferAttribute(d,e),a?Cr.addScaledVector(Qa,h):Cr.addScaledVector(Qa.sub(t),h))}t.add(Cr)}return t}raycast(e,t){const n=this.geometry,s=this.material,r=this.matrixWorld;s!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),wr.copy(n.boundingSphere),wr.applyMatrix4(r),Ci.copy(e.ray).recast(e.near),!(wr.containsPoint(Ci.origin)===!1&&(Ci.intersectSphere(wr,Fc)===null||Ci.origin.distanceToSquared(Fc)>(e.far-e.near)**2))&&(Oc.copy(r).invert(),Ci.copy(e.ray).applyMatrix4(Oc),!(n.boundingBox!==null&&Ci.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(e,t,Ci)))}_computeIntersections(e,t,n){let s;const r=this.geometry,a=this.material,o=r.index,l=r.attributes.position,c=r.attributes.uv,h=r.attributes.uv1,d=r.attributes.normal,u=r.groups,p=r.drawRange;if(o!==null)if(Array.isArray(a))for(let g=0,x=u.length;g<x;g++){const m=u[g],f=a[m.materialIndex],M=Math.max(m.start,p.start),E=Math.min(o.count,Math.min(m.start+m.count,p.start+p.count));for(let y=M,T=E;y<T;y+=3){const S=o.getX(y),R=o.getX(y+1),v=o.getX(y+2);s=Lr(this,f,e,n,c,h,d,S,R,v),s&&(s.faceIndex=Math.floor(y/3),s.face.materialIndex=m.materialIndex,t.push(s))}}else{const g=Math.max(0,p.start),x=Math.min(o.count,p.start+p.count);for(let m=g,f=x;m<f;m+=3){const M=o.getX(m),E=o.getX(m+1),y=o.getX(m+2);s=Lr(this,a,e,n,c,h,d,M,E,y),s&&(s.faceIndex=Math.floor(m/3),t.push(s))}}else if(l!==void 0)if(Array.isArray(a))for(let g=0,x=u.length;g<x;g++){const m=u[g],f=a[m.materialIndex],M=Math.max(m.start,p.start),E=Math.min(l.count,Math.min(m.start+m.count,p.start+p.count));for(let y=M,T=E;y<T;y+=3){const S=y,R=y+1,v=y+2;s=Lr(this,f,e,n,c,h,d,S,R,v),s&&(s.faceIndex=Math.floor(y/3),s.face.materialIndex=m.materialIndex,t.push(s))}}else{const g=Math.max(0,p.start),x=Math.min(l.count,p.start+p.count);for(let m=g,f=x;m<f;m+=3){const M=m,E=m+1,y=m+2;s=Lr(this,a,e,n,c,h,d,M,E,y),s&&(s.faceIndex=Math.floor(m/3),t.push(s))}}}}function jf(i,e,t,n,s,r,a,o){let l;if(e.side===rn?l=n.intersectTriangle(a,r,s,!0,o):l=n.intersectTriangle(s,r,a,e.side===vi,o),l===null)return null;Pr.copy(o),Pr.applyMatrix4(i.matrixWorld);const c=t.ray.origin.distanceTo(Pr);return c<t.near||c>t.far?null:{distance:c,point:Pr.clone(),object:i}}function Lr(i,e,t,n,s,r,a,o,l,c){i.getVertexPosition(o,Tr),i.getVertexPosition(l,Ar),i.getVertexPosition(c,Rr);const h=jf(i,e,t,n,Tr,Ar,Rr,kc);if(h){const d=new P;mn.getBarycoord(kc,Tr,Ar,Rr,d),s&&(h.uv=mn.getInterpolatedAttribute(s,o,l,c,d,new Fe)),r&&(h.uv1=mn.getInterpolatedAttribute(r,o,l,c,d,new Fe)),a&&(h.normal=mn.getInterpolatedAttribute(a,o,l,c,d,new P),h.normal.dot(n.direction)>0&&h.normal.multiplyScalar(-1));const u={a:o,b:l,c,normal:new P,materialIndex:0};mn.getNormal(Tr,Ar,Rr,u.normal),h.face=u,h.barycoord=d}return h}class hr extends Kt{constructor(e=null,t=1,n=1,s,r,a,o,l,c=Mt,h=Mt,d,u){super(null,a,o,l,c,h,s,r,d,u),this.isDataTexture=!0,this.image={data:e,width:t,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class Bc extends Mn{constructor(e,t,n,s=1){super(e,t,n),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=s}copy(e){return super.copy(e),this.meshPerAttribute=e.meshPerAttribute,this}toJSON(){const e=super.toJSON();return e.meshPerAttribute=this.meshPerAttribute,e.isInstancedBufferAttribute=!0,e}}const ts=new He,zc=new He,Dr=[],Hc=new zi,Jf=new He,Hs=new ht,Vs=new Ls;class Wt extends ht{constructor(e,t,n){super(e,t),this.isInstancedMesh=!0,this.instanceMatrix=new Bc(new Float32Array(n*16),16),this.instanceColor=null,this.morphTexture=null,this.count=n,this.boundingBox=null,this.boundingSphere=null;for(let s=0;s<n;s++)this.setMatrixAt(s,Jf)}computeBoundingBox(){const e=this.geometry,t=this.count;this.boundingBox===null&&(this.boundingBox=new zi),e.boundingBox===null&&e.computeBoundingBox(),this.boundingBox.makeEmpty();for(let n=0;n<t;n++)this.getMatrixAt(n,ts),Hc.copy(e.boundingBox).applyMatrix4(ts),this.boundingBox.union(Hc)}computeBoundingSphere(){const e=this.geometry,t=this.count;this.boundingSphere===null&&(this.boundingSphere=new Ls),e.boundingSphere===null&&e.computeBoundingSphere(),this.boundingSphere.makeEmpty();for(let n=0;n<t;n++)this.getMatrixAt(n,ts),Vs.copy(e.boundingSphere).applyMatrix4(ts),this.boundingSphere.union(Vs)}copy(e,t){return super.copy(e,t),this.instanceMatrix.copy(e.instanceMatrix),e.morphTexture!==null&&(this.morphTexture=e.morphTexture.clone()),e.instanceColor!==null&&(this.instanceColor=e.instanceColor.clone()),this.count=e.count,e.boundingBox!==null&&(this.boundingBox=e.boundingBox.clone()),e.boundingSphere!==null&&(this.boundingSphere=e.boundingSphere.clone()),this}getColorAt(e,t){return this.instanceColor===null?t.setRGB(1,1,1):t.fromArray(this.instanceColor.array,e*3)}getMatrixAt(e,t){return t.fromArray(this.instanceMatrix.array,e*16)}getMorphAt(e,t){const n=t.morphTargetInfluences,s=this.morphTexture.source.data.data,r=n.length+1,a=e*r+1;for(let o=0;o<n.length;o++)n[o]=s[a+o]}raycast(e,t){const n=this.matrixWorld,s=this.count;if(Hs.geometry=this.geometry,Hs.material=this.material,Hs.material!==void 0&&(this.boundingSphere===null&&this.computeBoundingSphere(),Vs.copy(this.boundingSphere),Vs.applyMatrix4(n),e.ray.intersectsSphere(Vs)!==!1))for(let r=0;r<s;r++){this.getMatrixAt(r,ts),zc.multiplyMatrices(n,ts),Hs.matrixWorld=zc,Hs.raycast(e,Dr);for(let a=0,o=Dr.length;a<o;a++){const l=Dr[a];l.instanceId=r,l.object=this,t.push(l)}Dr.length=0}}setColorAt(e,t){return this.instanceColor===null&&(this.instanceColor=new Bc(new Float32Array(this.instanceMatrix.count*3).fill(1),3)),t.toArray(this.instanceColor.array,e*3),this}setMatrixAt(e,t){return t.toArray(this.instanceMatrix.array,e*16),this}setMorphAt(e,t){const n=t.morphTargetInfluences,s=n.length+1;this.morphTexture===null&&(this.morphTexture=new hr(new Float32Array(s*this.count),s,this.count,lr,bn));const r=this.morphTexture.source.data.data;let a=0;for(let c=0;c<n.length;c++)a+=n[c];const o=this.geometry.morphTargetsRelative?1:1-a,l=s*e;return r[l]=o,r.set(n,l+1),this}updateMorphTargets(){}dispose(){this.dispatchEvent({type:"dispose"}),this.morphTexture!==null&&(this.morphTexture.dispose(),this.morphTexture=null)}}const eo=new P,Qf=new P,ep=new Xe;class ui{constructor(e=new P(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,n,s){return this.normal.set(e,t,n),this.constant=s,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,n){const s=eo.subVectors(n,t).cross(Qf.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(s,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,n=!0){const s=e.delta(eo),r=this.normal.dot(s);if(r===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;const a=-(e.start.dot(this.normal)+this.constant)/r;return n===!0&&(a<0||a>1)?null:t.copy(e.start).addScaledVector(s,a)}intersectsLine(e){const t=this.distanceToPoint(e.start),n=this.distanceToPoint(e.end);return t<0&&n>0||n<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){const n=t||ep.getNormalMatrix(e),s=this.coplanarPoint(eo).applyMatrix4(e),r=this.normal.applyMatrix3(n).normalize();return this.constant=-s.dot(r),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}}const Pi=new Ls,tp=new Fe(.5,.5),Ir=new P;class Hl{constructor(e=new ui,t=new ui,n=new ui,s=new ui,r=new ui,a=new ui){this.planes=[e,t,n,s,r,a]}set(e,t,n,s,r,a){const o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(n),o[3].copy(s),o[4].copy(r),o[5].copy(a),this}copy(e){const t=this.planes;for(let n=0;n<6;n++)t[n].copy(e.planes[n]);return this}setFromProjectionMatrix(e,t=Dn,n=!1){const s=this.planes,r=e.elements,a=r[0],o=r[1],l=r[2],c=r[3],h=r[4],d=r[5],u=r[6],p=r[7],g=r[8],x=r[9],m=r[10],f=r[11],M=r[12],E=r[13],y=r[14],T=r[15];if(s[0].setComponents(c-a,p-h,f-g,T-M).normalize(),s[1].setComponents(c+a,p+h,f+g,T+M).normalize(),s[2].setComponents(c+o,p+d,f+x,T+E).normalize(),s[3].setComponents(c-o,p-d,f-x,T-E).normalize(),n)s[4].setComponents(l,u,m,y).normalize(),s[5].setComponents(c-l,p-u,f-m,T-y).normalize();else if(s[4].setComponents(c-l,p-u,f-m,T-y).normalize(),t===Dn)s[5].setComponents(c+l,p+u,f+m,T+y).normalize();else if(t===sr)s[5].setComponents(l,u,m,y).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Pi.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),Pi.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Pi)}intersectsSprite(e){Pi.center.set(0,0,0);const t=tp.distanceTo(e.center);return Pi.radius=.7071067811865476+t,Pi.applyMatrix4(e.matrixWorld),this.intersectsSphere(Pi)}intersectsSphere(e){const t=this.planes,n=e.center,s=-e.radius;for(let r=0;r<6;r++)if(t[r].distanceToPoint(n)<s)return!1;return!0}intersectsBox(e){const t=this.planes;for(let n=0;n<6;n++){const s=t[n];if(Ir.x=s.normal.x>0?e.max.x:e.min.x,Ir.y=s.normal.y>0?e.max.y:e.min.y,Ir.z=s.normal.z>0?e.max.z:e.min.z,s.distanceToPoint(Ir)<0)return!1}return!0}containsPoint(e){const t=this.planes;for(let n=0;n<6;n++)if(t[n].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class Vl extends Ds{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new ye(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}const ha=new P,ua=new P,Vc=new He,Gs=new Ma,Nr=new Ls,to=new P,Gc=new P;class np extends Bt{constructor(e=new jt,t=new Vl){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,n=[0];for(let s=1,r=t.count;s<r;s++)ha.fromBufferAttribute(t,s-1),ua.fromBufferAttribute(t,s),n[s]=n[s-1],n[s]+=ha.distanceTo(ua);e.setAttribute("lineDistance",new St(n,1))}else ke("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(e,t){const n=this.geometry,s=this.matrixWorld,r=e.params.Line.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),Nr.copy(n.boundingSphere),Nr.applyMatrix4(s),Nr.radius+=r,e.ray.intersectsSphere(Nr)===!1)return;Vc.copy(s).invert(),Gs.copy(e.ray).applyMatrix4(Vc);const o=r/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,h=n.index,u=n.attributes.position;if(h!==null){const p=Math.max(0,a.start),g=Math.min(h.count,a.start+a.count);for(let x=p,m=g-1;x<m;x+=c){const f=h.getX(x),M=h.getX(x+1),E=Ur(this,e,Gs,l,f,M,x);E&&t.push(E)}if(this.isLineLoop){const x=h.getX(g-1),m=h.getX(p),f=Ur(this,e,Gs,l,x,m,g-1);f&&t.push(f)}}else{const p=Math.max(0,a.start),g=Math.min(u.count,a.start+a.count);for(let x=p,m=g-1;x<m;x+=c){const f=Ur(this,e,Gs,l,x,x+1,x);f&&t.push(f)}if(this.isLineLoop){const x=Ur(this,e,Gs,l,g-1,p,g-1);x&&t.push(x)}}}updateMorphTargets(){const t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){const s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){const o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}}function Ur(i,e,t,n,s,r,a){const o=i.geometry.attributes.position;if(ha.fromBufferAttribute(o,s),ua.fromBufferAttribute(o,r),t.distanceSqToSegment(ha,ua,to,Gc)>n)return;to.applyMatrix4(i.matrixWorld);const c=e.ray.origin.distanceTo(to);if(!(c<e.near||c>e.far))return{distance:c,point:Gc.clone().applyMatrix4(i.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:i}}const Wc=new P,$c=new P;class Yu extends np{constructor(e,t){super(e,t),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,n=[];for(let s=0,r=t.count;s<r;s+=2)Wc.fromBufferAttribute(t,s),$c.fromBufferAttribute(t,s+1),n[s]=s===0?0:n[s-1],n[s+1]=n[s]+Wc.distanceTo($c);e.setAttribute("lineDistance",new St(n,1))}else ke("LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class Zu extends Kt{constructor(e=[],t=Fi,n,s,r,a,o,l,c,h){super(e,t,n,s,r,a,o,l,c,h),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class Ku extends Kt{constructor(e,t,n,s,r,a,o,l,c){super(e,t,n,s,r,a,o,l,c),this.isCanvasTexture=!0,this.needsUpdate=!0}}class Ms extends Kt{constructor(e,t,n=On,s,r,a,o=Mt,l=Mt,c,h=jn,d=1){if(h!==jn&&h!==Ui)throw new Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const u={width:e,height:t,depth:d};super(u,s,r,a,o,l,h,n,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new Bl(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}}class ip extends Ms{constructor(e,t=On,n=Fi,s,r,a=Mt,o=Mt,l,c=jn){const h={width:e,height:e,depth:1},d=[h,h,h,h,h,h];super(e,e,t,n,s,r,a,o,l,c),this.image=d,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class ju extends Kt{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class Tt extends jt{constructor(e=1,t=1,n=1,s=1,r=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:n,widthSegments:s,heightSegments:r,depthSegments:a};const o=this;s=Math.floor(s),r=Math.floor(r),a=Math.floor(a);const l=[],c=[],h=[],d=[];let u=0,p=0;g("z","y","x",-1,-1,n,t,e,a,r,0),g("z","y","x",1,-1,n,t,-e,a,r,1),g("x","z","y",1,1,e,n,t,s,a,2),g("x","z","y",1,-1,e,n,-t,s,a,3),g("x","y","z",1,-1,e,t,n,s,r,4),g("x","y","z",-1,-1,e,t,-n,s,r,5),this.setIndex(l),this.setAttribute("position",new St(c,3)),this.setAttribute("normal",new St(h,3)),this.setAttribute("uv",new St(d,2));function g(x,m,f,M,E,y,T,S,R,v,w){const C=y/R,L=T/v,N=y/2,V=T/2,$=S/2,F=R+1,W=v+1;let G=0,J=0;const te=new P;for(let oe=0;oe<W;oe++){const me=oe*L-V;for(let be=0;be<F;be++){const at=be*C-N;te[x]=at*M,te[m]=me*E,te[f]=$,c.push(te.x,te.y,te.z),te[x]=0,te[m]=0,te[f]=S>0?1:-1,h.push(te.x,te.y,te.z),d.push(be/R),d.push(1-oe/v),G+=1}}for(let oe=0;oe<v;oe++)for(let me=0;me<R;me++){const be=u+me+F*oe,at=u+me+F*(oe+1),gt=u+(me+1)+F*(oe+1),it=u+(me+1)+F*oe;l.push(be,at,it),l.push(at,gt,it),J+=6}o.addGroup(p,J,w),p+=J,u+=G}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Tt(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class Hi extends jt{constructor(e=1,t=1,n=1,s=32,r=1,a=!1,o=0,l=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:e,radiusBottom:t,height:n,radialSegments:s,heightSegments:r,openEnded:a,thetaStart:o,thetaLength:l};const c=this;s=Math.floor(s),r=Math.floor(r);const h=[],d=[],u=[],p=[];let g=0;const x=[],m=n/2;let f=0;M(),a===!1&&(e>0&&E(!0),t>0&&E(!1)),this.setIndex(h),this.setAttribute("position",new St(d,3)),this.setAttribute("normal",new St(u,3)),this.setAttribute("uv",new St(p,2));function M(){const y=new P,T=new P;let S=0;const R=(t-e)/n;for(let v=0;v<=r;v++){const w=[],C=v/r,L=C*(t-e)+e;for(let N=0;N<=s;N++){const V=N/s,$=V*l+o,F=Math.sin($),W=Math.cos($);T.x=L*F,T.y=-C*n+m,T.z=L*W,d.push(T.x,T.y,T.z),y.set(F,R,W).normalize(),u.push(y.x,y.y,y.z),p.push(V,1-C),w.push(g++)}x.push(w)}for(let v=0;v<s;v++)for(let w=0;w<r;w++){const C=x[w][v],L=x[w+1][v],N=x[w+1][v+1],V=x[w][v+1];(e>0||w!==0)&&(h.push(C,L,V),S+=3),(t>0||w!==r-1)&&(h.push(L,N,V),S+=3)}c.addGroup(f,S,0),f+=S}function E(y){const T=g,S=new Fe,R=new P;let v=0;const w=y===!0?e:t,C=y===!0?1:-1;for(let N=1;N<=s;N++)d.push(0,m*C,0),u.push(0,C,0),p.push(.5,.5),g++;const L=g;for(let N=0;N<=s;N++){const $=N/s*l+o,F=Math.cos($),W=Math.sin($);R.x=w*W,R.y=m*C,R.z=w*F,d.push(R.x,R.y,R.z),u.push(0,C,0),S.x=F*.5+.5,S.y=W*.5*C+.5,p.push(S.x,S.y),g++}for(let N=0;N<s;N++){const V=T+N,$=L+N;y===!0?h.push($,$+1,V):h.push($+1,$,V),v+=3}c.addGroup(f,v,y===!0?1:2),f+=v}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Hi(e.radiusTop,e.radiusBottom,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}}class Is extends Hi{constructor(e=1,t=1,n=32,s=1,r=!1,a=0,o=Math.PI*2){super(0,e,t,n,s,r,a,o),this.type="ConeGeometry",this.parameters={radius:e,height:t,radialSegments:n,heightSegments:s,openEnded:r,thetaStart:a,thetaLength:o}}static fromJSON(e){return new Is(e.radius,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}}class Gl extends jt{constructor(e=[],t=[],n=1,s=0){super(),this.type="PolyhedronGeometry",this.parameters={vertices:e,indices:t,radius:n,detail:s};const r=[],a=[];o(s),c(n),h(),this.setAttribute("position",new St(r,3)),this.setAttribute("normal",new St(r.slice(),3)),this.setAttribute("uv",new St(a,2)),s===0?this.computeVertexNormals():this.normalizeNormals();function o(M){const E=new P,y=new P,T=new P;for(let S=0;S<t.length;S+=3)p(t[S+0],E),p(t[S+1],y),p(t[S+2],T),l(E,y,T,M)}function l(M,E,y,T){const S=T+1,R=[];for(let v=0;v<=S;v++){R[v]=[];const w=M.clone().lerp(y,v/S),C=E.clone().lerp(y,v/S),L=S-v;for(let N=0;N<=L;N++)N===0&&v===S?R[v][N]=w:R[v][N]=w.clone().lerp(C,N/L)}for(let v=0;v<S;v++)for(let w=0;w<2*(S-v)-1;w++){const C=Math.floor(w/2);w%2===0?(u(R[v][C+1]),u(R[v+1][C]),u(R[v][C])):(u(R[v][C+1]),u(R[v+1][C+1]),u(R[v+1][C]))}}function c(M){const E=new P;for(let y=0;y<r.length;y+=3)E.x=r[y+0],E.y=r[y+1],E.z=r[y+2],E.normalize().multiplyScalar(M),r[y+0]=E.x,r[y+1]=E.y,r[y+2]=E.z}function h(){const M=new P;for(let E=0;E<r.length;E+=3){M.x=r[E+0],M.y=r[E+1],M.z=r[E+2];const y=m(M)/2/Math.PI+.5,T=f(M)/Math.PI+.5;a.push(y,1-T)}g(),d()}function d(){for(let M=0;M<a.length;M+=6){const E=a[M+0],y=a[M+2],T=a[M+4],S=Math.max(E,y,T),R=Math.min(E,y,T);S>.9&&R<.1&&(E<.2&&(a[M+0]+=1),y<.2&&(a[M+2]+=1),T<.2&&(a[M+4]+=1))}}function u(M){r.push(M.x,M.y,M.z)}function p(M,E){const y=M*3;E.x=e[y+0],E.y=e[y+1],E.z=e[y+2]}function g(){const M=new P,E=new P,y=new P,T=new P,S=new Fe,R=new Fe,v=new Fe;for(let w=0,C=0;w<r.length;w+=9,C+=6){M.set(r[w+0],r[w+1],r[w+2]),E.set(r[w+3],r[w+4],r[w+5]),y.set(r[w+6],r[w+7],r[w+8]),S.set(a[C+0],a[C+1]),R.set(a[C+2],a[C+3]),v.set(a[C+4],a[C+5]),T.copy(M).add(E).add(y).divideScalar(3);const L=m(T);x(S,C+0,M,L),x(R,C+2,E,L),x(v,C+4,y,L)}}function x(M,E,y,T){T<0&&M.x===1&&(a[E]=M.x-1),y.x===0&&y.z===0&&(a[E]=T/2/Math.PI+.5)}function m(M){return Math.atan2(M.z,-M.x)}function f(M){return Math.atan2(-M.y,Math.sqrt(M.x*M.x+M.z*M.z))}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Gl(e.vertices,e.indices,e.radius,e.detail)}}const Or=new P,Fr=new P,no=new P,kr=new mn;class Ju extends jt{constructor(e=null,t=1){if(super(),this.type="EdgesGeometry",this.parameters={geometry:e,thresholdAngle:t},e!==null){const s=Math.pow(10,4),r=Math.cos(Qs*t),a=e.getIndex(),o=e.getAttribute("position"),l=a?a.count:o.count,c=[0,0,0],h=["a","b","c"],d=new Array(3),u={},p=[];for(let g=0;g<l;g+=3){a?(c[0]=a.getX(g),c[1]=a.getX(g+1),c[2]=a.getX(g+2)):(c[0]=g,c[1]=g+1,c[2]=g+2);const{a:x,b:m,c:f}=kr;if(x.fromBufferAttribute(o,c[0]),m.fromBufferAttribute(o,c[1]),f.fromBufferAttribute(o,c[2]),kr.getNormal(no),d[0]=`${Math.round(x.x*s)},${Math.round(x.y*s)},${Math.round(x.z*s)}`,d[1]=`${Math.round(m.x*s)},${Math.round(m.y*s)},${Math.round(m.z*s)}`,d[2]=`${Math.round(f.x*s)},${Math.round(f.y*s)},${Math.round(f.z*s)}`,!(d[0]===d[1]||d[1]===d[2]||d[2]===d[0]))for(let M=0;M<3;M++){const E=(M+1)%3,y=d[M],T=d[E],S=kr[h[M]],R=kr[h[E]],v=`${y}_${T}`,w=`${T}_${y}`;w in u&&u[w]?(no.dot(u[w].normal)<=r&&(p.push(S.x,S.y,S.z),p.push(R.x,R.y,R.z)),u[w]=null):v in u||(u[v]={index0:c[M],index1:c[E],normal:no.clone()})}}for(const g in u)if(u[g]){const{index0:x,index1:m}=u[g];Or.fromBufferAttribute(o,x),Fr.fromBufferAttribute(o,m),p.push(Or.x,Or.y,Or.z),p.push(Fr.x,Fr.y,Fr.z)}this.setAttribute("position",new St(p,3))}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}}class Wl extends Gl{constructor(e=1,t=0){const n=[1,0,0,-1,0,0,0,1,0,0,-1,0,0,0,1,0,0,-1],s=[0,2,4,0,4,3,0,3,5,0,5,2,1,2,5,1,5,3,1,3,4,1,4,2];super(n,s,e,t),this.type="OctahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new Wl(e.radius,e.detail)}}class un extends jt{constructor(e=1,t=1,n=1,s=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:n,heightSegments:s};const r=e/2,a=t/2,o=Math.floor(n),l=Math.floor(s),c=o+1,h=l+1,d=e/o,u=t/l,p=[],g=[],x=[],m=[];for(let f=0;f<h;f++){const M=f*u-a;for(let E=0;E<c;E++){const y=E*d-r;g.push(y,-M,0),x.push(0,0,1),m.push(E/o),m.push(1-f/l)}}for(let f=0;f<l;f++)for(let M=0;M<o;M++){const E=M+c*f,y=M+c*(f+1),T=M+1+c*(f+1),S=M+1+c*f;p.push(E,y,S),p.push(y,T,S)}this.setIndex(p),this.setAttribute("position",new St(g,3)),this.setAttribute("normal",new St(x,3)),this.setAttribute("uv",new St(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new un(e.width,e.height,e.widthSegments,e.heightSegments)}}class ur extends jt{constructor(e=1,t=32,n=16,s=0,r=Math.PI*2,a=0,o=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:t,heightSegments:n,phiStart:s,phiLength:r,thetaStart:a,thetaLength:o},t=Math.max(3,Math.floor(t)),n=Math.max(2,Math.floor(n));const l=Math.min(a+o,Math.PI);let c=0;const h=[],d=new P,u=new P,p=[],g=[],x=[],m=[];for(let f=0;f<=n;f++){const M=[],E=f/n,y=a+E*o,T=e*Math.cos(y),S=Math.sqrt(e*e-T*T);let R=0;f===0&&a===0?R=.5/t:f===n&&l===Math.PI&&(R=-.5/t);for(let v=0;v<=t;v++){const w=v/t,C=s+w*r;d.x=-S*Math.cos(C),d.y=T,d.z=S*Math.sin(C),g.push(d.x,d.y,d.z),u.copy(d).normalize(),x.push(u.x,u.y,u.z),m.push(w+R,1-E),M.push(c++)}h.push(M)}for(let f=0;f<n;f++)for(let M=0;M<t;M++){const E=h[f][M+1],y=h[f][M],T=h[f+1][M],S=h[f+1][M+1];(f!==0||a>0)&&p.push(E,y,S),(f!==n-1||l<Math.PI)&&p.push(y,T,S)}this.setIndex(p),this.setAttribute("position",new St(g,3)),this.setAttribute("normal",new St(x,3)),this.setAttribute("uv",new St(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new ur(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}}class $l extends jt{constructor(e=1,t=.4,n=12,s=48,r=Math.PI*2,a=0,o=Math.PI*2){super(),this.type="TorusGeometry",this.parameters={radius:e,tube:t,radialSegments:n,tubularSegments:s,arc:r,thetaStart:a,thetaLength:o},n=Math.floor(n),s=Math.floor(s);const l=[],c=[],h=[],d=[],u=new P,p=new P,g=new P;for(let x=0;x<=n;x++){const m=a+x/n*o;for(let f=0;f<=s;f++){const M=f/s*r;p.x=(e+t*Math.cos(m))*Math.cos(M),p.y=(e+t*Math.cos(m))*Math.sin(M),p.z=t*Math.sin(m),c.push(p.x,p.y,p.z),u.x=e*Math.cos(M),u.y=e*Math.sin(M),g.subVectors(p,u).normalize(),h.push(g.x,g.y,g.z),d.push(f/s),d.push(x/n)}}for(let x=1;x<=n;x++)for(let m=1;m<=s;m++){const f=(s+1)*x+m-1,M=(s+1)*(x-1)+m-1,E=(s+1)*(x-1)+m,y=(s+1)*x+m;l.push(f,M,y),l.push(M,E,y)}this.setIndex(l),this.setAttribute("position",new St(c,3)),this.setAttribute("normal",new St(h,3)),this.setAttribute("uv",new St(d,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new $l(e.radius,e.tube,e.radialSegments,e.tubularSegments,e.arc)}}function Ss(i){const e={};for(const t in i){e[t]={};for(const n in i[t]){const s=i[t][n];if(Xc(s))s.isRenderTargetTexture?(ke("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][n]=null):e[t][n]=s.clone();else if(Array.isArray(s))if(Xc(s[0])){const r=[];for(let a=0,o=s.length;a<o;a++)r[a]=s[a].clone();e[t][n]=r}else e[t][n]=s.slice();else e[t][n]=s}}return e}function Jt(i){const e={};for(let t=0;t<i.length;t++){const n=Ss(i[t]);for(const s in n)e[s]=n[s]}return e}function Xc(i){return i&&(i.isColor||i.isMatrix3||i.isMatrix4||i.isVector2||i.isVector3||i.isVector4||i.isTexture||i.isQuaternion)}function sp(i){const e=[];for(let t=0;t<i.length;t++)e.push(i[t].clone());return e}function Qu(i){const e=i.getRenderTarget();return e===null?i.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:et.workingColorSpace}const rp={clone:Ss,merge:Jt};var ap=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,op=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class En extends Ds{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=ap,this.fragmentShader=op,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Ss(e.uniforms),this.uniformsGroups=sp(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){const t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(const s in this.uniforms){const a=this.uniforms[s].value;a&&a.isTexture?t.uniforms[s]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[s]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[s]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[s]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[s]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[s]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[s]={type:"m4",value:a.toArray()}:t.uniforms[s]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;const n={};for(const s in this.extensions)this.extensions[s]===!0&&(n[s]=!0);return Object.keys(n).length>0&&(t.extensions=n),t}fromJSON(e,t){if(super.fromJSON(e,t),e.uniforms!==void 0)for(const n in e.uniforms){const s=e.uniforms[n];switch(this.uniforms[n]={},s.type){case"t":this.uniforms[n].value=t[s.value]||null;break;case"c":this.uniforms[n].value=new ye().setHex(s.value);break;case"v2":this.uniforms[n].value=new Fe().fromArray(s.value);break;case"v3":this.uniforms[n].value=new P().fromArray(s.value);break;case"v4":this.uniforms[n].value=new At().fromArray(s.value);break;case"m3":this.uniforms[n].value=new Xe().fromArray(s.value);break;case"m4":this.uniforms[n].value=new He().fromArray(s.value);break;default:this.uniforms[n].value=s.value}}if(e.defines!==void 0&&(this.defines=e.defines),e.vertexShader!==void 0&&(this.vertexShader=e.vertexShader),e.fragmentShader!==void 0&&(this.fragmentShader=e.fragmentShader),e.glslVersion!==void 0&&(this.glslVersion=e.glslVersion),e.extensions!==void 0)for(const n in e.extensions)this.extensions[n]=e.extensions[n];return e.lights!==void 0&&(this.lights=e.lights),e.clipping!==void 0&&(this.clipping=e.clipping),this}}class lp extends En{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class vs extends Ds{constructor(e){super(),this.isMeshLambertMaterial=!0,this.type="MeshLambertMaterial",this.color=new ye(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new ye(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=ul,this.normalScale=new Fe(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new xi,this.combine=Pl,this.reflectivity=1,this.envMapIntensity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.envMapIntensity=e.envMapIntensity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}}class cp extends Ds{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=xf,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class hp extends Ds{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}class Xl extends Bt{constructor(e,t=1){super(),this.isLight=!0,this.type="Light",this.color=new ye(e),this.intensity=t}dispose(){this.dispatchEvent({type:"dispose"})}copy(e,t){return super.copy(e,t),this.color.copy(e.color),this.intensity=e.intensity,this}toJSON(e){const t=super.toJSON(e);return t.object.color=this.color.getHex(),t.object.intensity=this.intensity,t}}class up extends Xl{constructor(e,t,n){super(e,n),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(Bt.DEFAULT_UP),this.updateMatrix(),this.groundColor=new ye(t)}copy(e,t){return super.copy(e,t),this.groundColor.copy(e.groundColor),this}toJSON(e){const t=super.toJSON(e);return t.object.groundColor=this.groundColor.getHex(),t}}const io=new He,qc=new P,Yc=new P;class ed{constructor(e){this.camera=e,this.intensity=1,this.bias=0,this.biasNode=null,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new Fe(512,512),this.mapType=hn,this.map=null,this.mapPass=null,this.matrix=new He,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new Hl,this._frameExtents=new Fe(1,1),this._viewportCount=1,this._viewports=[new At(0,0,1,1)]}getViewportCount(){return this._viewportCount}getFrustum(){return this._frustum}updateMatrices(e){const t=this.camera,n=this.matrix;qc.setFromMatrixPosition(e.matrixWorld),t.position.copy(qc),Yc.setFromMatrixPosition(e.target.matrixWorld),t.lookAt(Yc),t.updateMatrixWorld(),io.multiplyMatrices(t.projectionMatrix,t.matrixWorldInverse),this._frustum.setFromProjectionMatrix(io,t.coordinateSystem,t.reversedDepth),t.coordinateSystem===sr||t.reversedDepth?n.set(.5,0,0,.5,0,.5,0,.5,0,0,1,0,0,0,0,1):n.set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1),n.multiply(io)}getViewport(e){return this._viewports[e]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(e){return this.camera=e.camera.clone(),this.intensity=e.intensity,this.bias=e.bias,this.radius=e.radius,this.autoUpdate=e.autoUpdate,this.needsUpdate=e.needsUpdate,this.normalBias=e.normalBias,this.blurSamples=e.blurSamples,this.mapSize.copy(e.mapSize),this.biasNode=e.biasNode,this}clone(){return new this.constructor().copy(this)}toJSON(){const e={};return this.intensity!==1&&(e.intensity=this.intensity),this.bias!==0&&(e.bias=this.bias),this.normalBias!==0&&(e.normalBias=this.normalBias),this.radius!==1&&(e.radius=this.radius),(this.mapSize.x!==512||this.mapSize.y!==512)&&(e.mapSize=this.mapSize.toArray()),e.camera=this.camera.toJSON(!1).object,delete e.camera.matrix,e}}const Br=new P,zr=new Sn,Rn=new P;class td extends Bt{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new He,this.projectionMatrix=new He,this.projectionMatrixInverse=new He,this.coordinateSystem=Dn,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Br,zr,Rn),Rn.x===1&&Rn.y===1&&Rn.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Br,zr,Rn.set(1,1,1)).invert()}updateWorldMatrix(e,t,n=!1){super.updateWorldMatrix(e,t,n),this.matrixWorld.decompose(Br,zr,Rn),Rn.x===1&&Rn.y===1&&Rn.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Br,zr,Rn.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}const li=new P,Zc=new Fe,Kc=new Fe;class cn extends td{constructor(e=50,t=1,n=.1,s=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=n,this.far=s,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const t=.5*this.getFilmHeight()/e;this.fov=dl*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(Qs*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return dl*2*Math.atan(Math.tan(Qs*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,n){li.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(li.x,li.y).multiplyScalar(-e/li.z),li.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(li.x,li.y).multiplyScalar(-e/li.z)}getViewSize(e,t){return this.getViewBounds(e,Zc,Kc),t.subVectors(Kc,Zc)}setViewOffset(e,t,n,s,r,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let t=e*Math.tan(Qs*.5*this.fov)/this.zoom,n=2*t,s=this.aspect*n,r=-.5*s;const a=this.view;if(this.view!==null&&this.view.enabled){const l=a.fullWidth,c=a.fullHeight;r+=a.offsetX*s/l,t-=a.offsetY*n/c,s*=a.width/l,n*=a.height/c}const o=this.filmOffset;o!==0&&(r+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(r,r+s,t,t-n,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}}class dp extends ed{constructor(){super(new cn(90,1,.5,500)),this.isPointLightShadow=!0}}class fp extends Xl{constructor(e,t,n=0,s=2){super(e,t),this.isPointLight=!0,this.type="PointLight",this.distance=n,this.decay=s,this.shadow=new dp}get power(){return this.intensity*4*Math.PI}set power(e){this.intensity=e/(4*Math.PI)}dispose(){super.dispose(),this.shadow.dispose()}copy(e,t){return super.copy(e,t),this.distance=e.distance,this.decay=e.decay,this.shadow=e.shadow.clone(),this}toJSON(e){const t=super.toJSON(e);return t.object.distance=this.distance,t.object.decay=this.decay,t.object.shadow=this.shadow.toJSON(),t}}class ql extends td{constructor(e=-1,t=1,n=1,s=-1,r=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=n,this.bottom=s,this.near=r,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,n,s,r,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,s=(this.top+this.bottom)/2;let r=n-e,a=n+e,o=s+t,l=s-t;if(this.view!==null&&this.view.enabled){const c=(this.right-this.left)/this.view.fullWidth/this.zoom,h=(this.top-this.bottom)/this.view.fullHeight/this.zoom;r+=c*this.view.offsetX,a=r+c*this.view.width,o-=h*this.view.offsetY,l=o-h*this.view.height}this.projectionMatrix.makeOrthographic(r,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}}class pp extends ed{constructor(){super(new ql(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}}class mp extends Xl{constructor(e,t){super(e,t),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(Bt.DEFAULT_UP),this.updateMatrix(),this.target=new Bt,this.shadow=new pp}dispose(){super.dispose(),this.shadow.dispose()}copy(e){return super.copy(e),this.target=e.target.clone(),this.shadow=e.shadow.clone(),this}toJSON(e){const t=super.toJSON(e);return t.object.shadow=this.shadow.toJSON(),t.object.target=this.target.uuid,t}}const ns=-90,is=1;class gp extends Bt{constructor(e,t,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;const s=new cn(ns,is,e,t);s.layers=this.layers,this.add(s);const r=new cn(ns,is,e,t);r.layers=this.layers,this.add(r);const a=new cn(ns,is,e,t);a.layers=this.layers,this.add(a);const o=new cn(ns,is,e,t);o.layers=this.layers,this.add(o);const l=new cn(ns,is,e,t);l.layers=this.layers,this.add(l);const c=new cn(ns,is,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){const e=this.coordinateSystem,t=this.children.concat(),[n,s,r,a,o,l]=t;for(const c of t)this.remove(c);if(e===Dn)n.up.set(0,1,0),n.lookAt(1,0,0),s.up.set(0,1,0),s.lookAt(-1,0,0),r.up.set(0,0,-1),r.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===sr)n.up.set(0,-1,0),n.lookAt(-1,0,0),s.up.set(0,-1,0),s.lookAt(1,0,0),r.up.set(0,0,1),r.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();const{renderTarget:n,activeMipmapLevel:s}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[r,a,o,l,c,h]=this.children,d=e.getRenderTarget(),u=e.getActiveCubeFace(),p=e.getActiveMipmapLevel(),g=e.xr.enabled;e.xr.enabled=!1;const x=n.texture.generateMipmaps;n.texture.generateMipmaps=!1;let m=!1;e.isWebGLRenderer===!0?m=e.state.buffers.depth.getReversed():m=e.reversedDepthBuffer,e.setRenderTarget(n,0,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,r),e.setRenderTarget(n,1,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,a),e.setRenderTarget(n,2,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,o),e.setRenderTarget(n,3,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,l),e.setRenderTarget(n,4,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,c),n.texture.generateMipmaps=x,e.setRenderTarget(n,5,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,h),e.setRenderTarget(d,u,p),e.xr.enabled=g,n.texture.needsPMREMUpdate=!0}}class _p extends cn{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}const jc=new He;class vp{constructor(e,t,n=0,s=1/0){this.ray=new Ma(e,t),this.near=n,this.far=s,this.camera=null,this.layers=new zl,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,t){this.ray.set(e,t)}setFromCamera(e,t){t.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(t.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(t).sub(this.ray.origin).normalize(),this.camera=t):t.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,t.projectionMatrix.elements[14]).unproject(t),this.ray.direction.set(0,0,-1).transformDirection(t.matrixWorld),this.camera=t):st("Raycaster: Unsupported camera type: "+t.type)}setFromXRController(e){return jc.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(jc),this}intersectObject(e,t=!0,n=[]){return fl(e,this,n,t),n.sort(Jc),n}intersectObjects(e,t=!0,n=[]){for(let s=0,r=e.length;s<r;s++)fl(e[s],this,n,t);return n.sort(Jc),n}}function Jc(i,e){return i.distance-e.distance}function fl(i,e,t,n){let s=!0;if(i.layers.test(e.layers)&&i.raycast(e,t)===!1&&(s=!1),s===!0&&n===!0){const r=i.children;for(let a=0,o=r.length;a<o;a++)fl(r[a],e,t,!0)}}class xp{constructor(e=!0){this.autoStart=e,this.startTime=0,this.oldTime=0,this.elapsedTime=0,this.running=!1,ke("Clock: This module has been deprecated. Please use THREE.Timer instead.")}start(){this.startTime=performance.now(),this.oldTime=this.startTime,this.elapsedTime=0,this.running=!0}stop(){this.getElapsedTime(),this.running=!1,this.autoStart=!1}getElapsedTime(){return this.getDelta(),this.elapsedTime}getDelta(){let e=0;if(this.autoStart&&!this.running)return this.start(),0;if(this.running){const t=performance.now();e=(t-this.oldTime)/1e3,this.oldTime=t,this.elapsedTime+=e}return e}}class Qc{constructor(e=1,t=0,n=0){this.radius=e,this.phi=t,this.theta=n}set(e,t,n){return this.radius=e,this.phi=t,this.theta=n,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=Qe(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,t,n){return this.radius=Math.sqrt(e*e+t*t+n*n),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,n),this.phi=Math.acos(Qe(t/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}}const ac=class ac{constructor(e,t,n,s){this.elements=[1,0,0,1],e!==void 0&&this.set(e,t,n,s)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let n=0;n<4;n++)this.elements[n]=e[n+t];return this}set(e,t,n,s){const r=this.elements;return r[0]=e,r[2]=t,r[1]=n,r[3]=s,this}};ac.prototype.isMatrix2=!0;let eh=ac;class nd extends Ei{constructor(e,t=null){super(),this.object=e,this.domElement=t,this.enabled=!0,this.state=-1,this.keys={},this.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null},this.touches={ONE:null,TWO:null}}connect(e){if(e===void 0){ke("Controls: connect() now requires an element.");return}this.domElement!==null&&this.disconnect(),this.domElement=e}disconnect(){}dispose(){}update(){}}function th(i,e,t,n){const s=yp(n);switch(t){case Hu:return i*e;case lr:return i*e/s.components*s.byteLength;case Nl:return i*e/s.components*s.byteLength;case ki:return i*e*2/s.components*s.byteLength;case Ul:return i*e*2/s.components*s.byteLength;case Vu:return i*e*3/s.components*s.byteLength;case gn:return i*e*4/s.components*s.byteLength;case Ol:return i*e*4/s.components*s.byteLength;case Qr:case ea:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case ta:case na:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Oo:case ko:return Math.max(i,16)*Math.max(e,8)/4;case Uo:case Fo:return Math.max(i,8)*Math.max(e,8)/2;case Bo:case zo:case Vo:case Go:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case Ho:case ra:case Wo:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case $o:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Xo:return Math.floor((i+4)/5)*Math.floor((e+3)/4)*16;case qo:return Math.floor((i+4)/5)*Math.floor((e+4)/5)*16;case Yo:return Math.floor((i+5)/6)*Math.floor((e+4)/5)*16;case Zo:return Math.floor((i+5)/6)*Math.floor((e+5)/6)*16;case Ko:return Math.floor((i+7)/8)*Math.floor((e+4)/5)*16;case jo:return Math.floor((i+7)/8)*Math.floor((e+5)/6)*16;case Jo:return Math.floor((i+7)/8)*Math.floor((e+7)/8)*16;case Qo:return Math.floor((i+9)/10)*Math.floor((e+4)/5)*16;case el:return Math.floor((i+9)/10)*Math.floor((e+5)/6)*16;case tl:return Math.floor((i+9)/10)*Math.floor((e+7)/8)*16;case nl:return Math.floor((i+9)/10)*Math.floor((e+9)/10)*16;case il:return Math.floor((i+11)/12)*Math.floor((e+9)/10)*16;case sl:return Math.floor((i+11)/12)*Math.floor((e+11)/12)*16;case rl:case al:case ol:return Math.ceil(i/4)*Math.ceil(e/4)*16;case ll:case cl:return Math.ceil(i/4)*Math.ceil(e/4)*8;case aa:case hl:return Math.ceil(i/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function yp(i){switch(i){case hn:case Fu:return{byteLength:1,components:1};case nr:case ku:case Kn:return{byteLength:2,components:1};case Dl:case Il:return{byteLength:2,components:4};case On:case Ll:case bn:return{byteLength:4,components:1};case Bu:case zu:return{byteLength:4,components:3}}throw new Error(`THREE.TextureUtils: Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:Cl}}));typeof window<"u"&&(window.__THREE__?ke("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=Cl);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function id(){let i=null,e=!1,t=null,n=null;function s(r,a){t(r,a),n=i.requestAnimationFrame(s)}return{start:function(){e!==!0&&t!==null&&i!==null&&(n=i.requestAnimationFrame(s),e=!0)},stop:function(){i!==null&&i.cancelAnimationFrame(n),e=!1},setAnimationLoop:function(r){t=r},setContext:function(r){i=r}}}function bp(i){const e=new WeakMap;function t(o,l){const c=o.array,h=o.usage,d=c.byteLength,u=i.createBuffer();i.bindBuffer(l,u),i.bufferData(l,c,h),o.onUploadCallback();let p;if(c instanceof Float32Array)p=i.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)p=i.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?p=i.HALF_FLOAT:p=i.UNSIGNED_SHORT;else if(c instanceof Int16Array)p=i.SHORT;else if(c instanceof Uint32Array)p=i.UNSIGNED_INT;else if(c instanceof Int32Array)p=i.INT;else if(c instanceof Int8Array)p=i.BYTE;else if(c instanceof Uint8Array)p=i.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)p=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:u,type:p,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:d}}function n(o,l,c){const h=l.array,d=l.updateRanges;if(i.bindBuffer(c,o),d.length===0)i.bufferSubData(c,0,h);else{d.sort((p,g)=>p.start-g.start);let u=0;for(let p=1;p<d.length;p++){const g=d[u],x=d[p];x.start<=g.start+g.count+1?g.count=Math.max(g.count,x.start+x.count-g.start):(++u,d[u]=x)}d.length=u+1;for(let p=0,g=d.length;p<g;p++){const x=d[p];i.bufferSubData(c,x.start*h.BYTES_PER_ELEMENT,h,x.start,x.count)}l.clearUpdateRanges()}l.onUploadCallback()}function s(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function r(o){o.isInterleavedBufferAttribute&&(o=o.data);const l=e.get(o);l&&(i.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){const h=e.get(o);(!h||h.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}const c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(c.buffer,o,l),c.version=o.version}}return{get:s,remove:r,update:a}}var Mp=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,Sp=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,Ep=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,wp=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,Tp=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,Ap=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,Rp=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,Cp=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,Pp=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec4 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 );
	}
#endif`,Lp=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,Dp=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,Ip=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,Np=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,Up=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,Op=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,Fp=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,kp=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,Bp=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,zp=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,Hp=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,Vp=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,Gp=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,Wp=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec4( 1.0 );
#endif
#ifdef USE_COLOR_ALPHA
	vColor *= color;
#elif defined( USE_COLOR )
	vColor.rgb *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.rgb *= instanceColor.rgb;
#endif
#ifdef USE_BATCHING_COLOR
	vColor *= getBatchingColor( getIndirectIndex( gl_DrawID ) );
#endif`,$p=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
#define inverseTransformDirection transformDirectionByInverseViewMatrix
vec3 transformNormalByInverseViewMatrix( in vec3 normal, in mat4 viewMatrix ) {
	return normalize( ( vec4( normal, 0.0 ) * viewMatrix ).xyz );
}
vec3 transformDirectionByInverseViewMatrix( in vec3 dir, in mat4 viewMatrix ) {
	return normalize( ( vec4( dir, 0.0 ) * viewMatrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,Xp=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,qp=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
#endif`,Yp=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,Zp=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,Kp=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,jp=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,Jp="gl_FragColor = linearToOutputTexel( gl_FragColor );",Qp=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,em=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * reflectVec );
		#ifdef ENVMAP_BLENDING_MULTIPLY
			outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_MIX )
			outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_ADD )
			outgoingLight += envColor.xyz * specularStrength * reflectivity;
		#endif
	#endif
#endif`,tm=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,nm=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,im=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,sm=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,rm=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,am=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,om=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,lm=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,cm=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,hm=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,um=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,dm=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,fm=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif
#include <lightprobes_pars_fragment>`,pm=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = transformDirectionByInverseViewMatrix( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,mm=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,gm=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,_m=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,vm=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,xm=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,ym=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
		vec3 iridescenceFresnelDielectric;
		vec3 iridescenceFresnelMetallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		return 0.5 / max( gv + gl, EPSILON );
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
vec3 BRDF_GGX_Multiscatter( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 singleScatter = BRDF_GGX( lightDir, viewDir, normal, material );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 dfgV = texture2D( dfgLUT, vec2( material.roughness, dotNV ) ).rg;
	vec2 dfgL = texture2D( dfgLUT, vec2( material.roughness, dotNL ) ).rg;
	vec3 FssEss_V = material.specularColorBlended * dfgV.x + material.specularF90 * dfgV.y;
	vec3 FssEss_L = material.specularColorBlended * dfgL.x + material.specularF90 * dfgL.y;
	float Ess_V = dfgV.x + dfgV.y;
	float Ess_L = dfgL.x + dfgL.y;
	float Ems_V = 1.0 - Ess_V;
	float Ems_L = 1.0 - Ess_L;
	vec3 Favg = material.specularColorBlended + ( 1.0 - material.specularColorBlended ) * 0.047619;
	vec3 Fms = FssEss_V * FssEss_L * Favg / ( 1.0 - Ems_V * Ems_L * Favg + EPSILON );
	float compensationFactor = Ems_V * Ems_L;
	vec3 multiScatter = Fms * compensationFactor;
	return singleScatter + multiScatter;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( material.specularF90 - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
		#ifdef USE_CLEARCOAT
			vec3 Ncc = geometryClearcoatNormal;
			vec2 uvClearcoat = LTC_Uv( Ncc, viewDir, material.clearcoatRoughness );
			vec4 t1Clearcoat = texture2D( ltc_1, uvClearcoat );
			vec4 t2Clearcoat = texture2D( ltc_2, uvClearcoat );
			mat3 mInvClearcoat = mat3(
				vec3( t1Clearcoat.x, 0, t1Clearcoat.y ),
				vec3(             0, 1,             0 ),
				vec3( t1Clearcoat.z, 0, t1Clearcoat.w )
			);
			vec3 fresnelClearcoat = material.clearcoatF0 * t2Clearcoat.x + ( material.clearcoatF90 - material.clearcoatF0 ) * t2Clearcoat.y;
			clearcoatSpecularDirect += lightColor * fresnelClearcoat * LTC_Evaluate( Ncc, viewDir, position, mInvClearcoat, rectCoords );
		#endif
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
 
 		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
 
 		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
 		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );
 
 		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );
 
 		irradiance *= sheenEnergyComp;
 
 	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX_Multiscatter( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
 	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnelDielectric, material.roughness, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceFresnelMetallic, material.roughness, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( geometryNormal, geometryViewDir, material.diffuseColor, material.specularF90, material.roughness, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,bm=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( material.iridescenceFresnelDielectric, material.iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
	#ifdef USE_LIGHT_PROBES_GRID
		vec3 probeWorldPos = ( ( vec4( geometryPosition, 1.0 ) - viewMatrix[ 3 ] ) * viewMatrix ).xyz;
		vec3 probeWorldNormal = transformNormalByInverseViewMatrix( geometryNormal, viewMatrix );
		irradiance += getLightProbeGridIrradiance( probeWorldPos, probeWorldNormal );
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,Mm=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( ENVMAP_TYPE_CUBE_UV )
		#if defined( STANDARD ) || defined( LAMBERT ) || defined( PHONG )
			iblIrradiance += getIBLIrradiance( geometryNormal );
		#endif
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,Sm=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,Em=`#ifdef USE_LIGHT_PROBES_GRID
uniform highp sampler3D probesSH;
uniform vec3 probesMin;
uniform vec3 probesMax;
uniform vec3 probesResolution;
vec3 getLightProbeGridIrradiance( vec3 worldPos, vec3 worldNormal ) {
	vec3 res = probesResolution;
	vec3 gridRange = probesMax - probesMin;
	vec3 resMinusOne = res - 1.0;
	vec3 probeSpacing = gridRange / resMinusOne;
	vec3 samplePos = worldPos + worldNormal * probeSpacing * 0.5;
	vec3 uvw = clamp( ( samplePos - probesMin ) / gridRange, 0.0, 1.0 );
	uvw = uvw * resMinusOne / res + 0.5 / res;
	float nz          = res.z;
	float paddedSlices = nz + 2.0;
	float atlasDepth  = 7.0 * paddedSlices;
	float uvZBase     = uvw.z * nz + 1.0;
	vec4 s0 = texture( probesSH, vec3( uvw.xy, ( uvZBase                       ) / atlasDepth ) );
	vec4 s1 = texture( probesSH, vec3( uvw.xy, ( uvZBase +       paddedSlices   ) / atlasDepth ) );
	vec4 s2 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 2.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s3 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 3.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s4 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 4.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s5 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 5.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s6 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 6.0 * paddedSlices   ) / atlasDepth ) );
	vec3 c0 = s0.xyz;
	vec3 c1 = vec3( s0.w, s1.xy );
	vec3 c2 = vec3( s1.zw, s2.x );
	vec3 c3 = s2.yzw;
	vec3 c4 = s3.xyz;
	vec3 c5 = vec3( s3.w, s4.xy );
	vec3 c6 = vec3( s4.zw, s5.x );
	vec3 c7 = s5.yzw;
	vec3 c8 = s6.xyz;
	float x = worldNormal.x, y = worldNormal.y, z = worldNormal.z;
	vec3 result = c0 * 0.886227;
	result += c1 * 2.0 * 0.511664 * y;
	result += c2 * 2.0 * 0.511664 * z;
	result += c3 * 2.0 * 0.511664 * x;
	result += c4 * 2.0 * 0.429043 * x * y;
	result += c5 * 2.0 * 0.429043 * y * z;
	result += c6 * ( 0.743125 * z * z - 0.247708 );
	result += c7 * 2.0 * 0.429043 * x * z;
	result += c8 * 0.429043 * ( x * x - y * y );
	return max( result, vec3( 0.0 ) );
}
#endif`,wm=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,Tm=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Am=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Rm=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,Cm=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,Pm=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,Lm=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,Dm=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,Im=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,Nm=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,Um=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,Om=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,Fm=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,km=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,Bm=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,zm=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#ifdef DOUBLE_SIDED
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#ifdef DOUBLE_SIDED
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,Hm=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#if defined( USE_PACKED_NORMALMAP )
		mapN = vec3( mapN.xy, sqrt( saturate( 1.0 - dot( mapN.xy, mapN.xy ) ) ) );
	#endif
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,Vm=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Gm=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Wm=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,$m=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,Xm=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,qm=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,Ym=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,Zm=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,Km=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,jm=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	#ifdef USE_REVERSED_DEPTH_BUFFER
	
		return depth * ( far - near ) - far;
	#else
		return depth * ( near - far ) - near;
	#endif
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	
	#ifdef USE_REVERSED_DEPTH_BUFFER
		return ( near * far ) / ( ( near - far ) * depth - near );
	#else
		return ( near * far ) / ( ( far - near ) * depth - far );
	#endif
}`,Jm=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,Qm=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,eg=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,tg=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,ng=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,ig=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,sg=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif
				
				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			#ifdef USE_REVERSED_DEPTH_BUFFER
				float dp = ( shadowCameraNear * ( shadowCameraFar - viewSpaceZ ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp -= shadowBias;
			#else
				float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp += shadowBias;
			#endif
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
			vec2 sample0 = vogelDiskSample( 0, 5, phi );
			vec2 sample1 = vogelDiskSample( 1, 5, phi );
			vec2 sample2 = vogelDiskSample( 2, 5, phi );
			vec2 sample3 = vogelDiskSample( 3, 5, phi );
			vec2 sample4 = vogelDiskSample( 4, 5, phi );
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * sample0.x + bitangent * sample0.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample1.x + bitangent * sample1.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample2.x + bitangent * sample2.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample3.x + bitangent * sample3.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample4.x + bitangent * sample4.y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				depth = 1.0 - depth;
			#endif
			shadow = step( dp, depth );
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,rg=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,ag=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	#ifdef HAS_NORMAL
		vec3 shadowWorldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
	#else
		vec3 shadowWorldNormal = vec3( 0.0 );
	#endif
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,og=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,lg=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,cg=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,hg=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,ug=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,dg=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,fg=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,pg=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,mg=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,gg=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,_g=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,vg=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,xg=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,yg=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,bg=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const Mg=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,Sg=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Eg=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,wg=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vWorldDirection );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Tg=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,Ag=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Rg=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,Cg=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,Pg=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,Lg=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,Dg=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,Ig=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Ng=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,Ug=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Og=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,Fg=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,kg=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Bg=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,zg=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,Hg=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Vg=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,Gg=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,Wg=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,$g=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Xg=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,qg=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
 
		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;
 
 	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Yg=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Zg=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Kg=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,jg=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Jg=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Qg=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,e_=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,t_=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,Ze={alphahash_fragment:Mp,alphahash_pars_fragment:Sp,alphamap_fragment:Ep,alphamap_pars_fragment:wp,alphatest_fragment:Tp,alphatest_pars_fragment:Ap,aomap_fragment:Rp,aomap_pars_fragment:Cp,batching_pars_vertex:Pp,batching_vertex:Lp,begin_vertex:Dp,beginnormal_vertex:Ip,bsdfs:Np,iridescence_fragment:Up,bumpmap_pars_fragment:Op,clipping_planes_fragment:Fp,clipping_planes_pars_fragment:kp,clipping_planes_pars_vertex:Bp,clipping_planes_vertex:zp,color_fragment:Hp,color_pars_fragment:Vp,color_pars_vertex:Gp,color_vertex:Wp,common:$p,cube_uv_reflection_fragment:Xp,defaultnormal_vertex:qp,displacementmap_pars_vertex:Yp,displacementmap_vertex:Zp,emissivemap_fragment:Kp,emissivemap_pars_fragment:jp,colorspace_fragment:Jp,colorspace_pars_fragment:Qp,envmap_fragment:em,envmap_common_pars_fragment:tm,envmap_pars_fragment:nm,envmap_pars_vertex:im,envmap_physical_pars_fragment:pm,envmap_vertex:sm,fog_vertex:rm,fog_pars_vertex:am,fog_fragment:om,fog_pars_fragment:lm,gradientmap_pars_fragment:cm,lightmap_pars_fragment:hm,lights_lambert_fragment:um,lights_lambert_pars_fragment:dm,lights_pars_begin:fm,lights_toon_fragment:mm,lights_toon_pars_fragment:gm,lights_phong_fragment:_m,lights_phong_pars_fragment:vm,lights_physical_fragment:xm,lights_physical_pars_fragment:ym,lights_fragment_begin:bm,lights_fragment_maps:Mm,lights_fragment_end:Sm,lightprobes_pars_fragment:Em,logdepthbuf_fragment:wm,logdepthbuf_pars_fragment:Tm,logdepthbuf_pars_vertex:Am,logdepthbuf_vertex:Rm,map_fragment:Cm,map_pars_fragment:Pm,map_particle_fragment:Lm,map_particle_pars_fragment:Dm,metalnessmap_fragment:Im,metalnessmap_pars_fragment:Nm,morphinstance_vertex:Um,morphcolor_vertex:Om,morphnormal_vertex:Fm,morphtarget_pars_vertex:km,morphtarget_vertex:Bm,normal_fragment_begin:zm,normal_fragment_maps:Hm,normal_pars_fragment:Vm,normal_pars_vertex:Gm,normal_vertex:Wm,normalmap_pars_fragment:$m,clearcoat_normal_fragment_begin:Xm,clearcoat_normal_fragment_maps:qm,clearcoat_pars_fragment:Ym,iridescence_pars_fragment:Zm,opaque_fragment:Km,packing:jm,premultiplied_alpha_fragment:Jm,project_vertex:Qm,dithering_fragment:eg,dithering_pars_fragment:tg,roughnessmap_fragment:ng,roughnessmap_pars_fragment:ig,shadowmap_pars_fragment:sg,shadowmap_pars_vertex:rg,shadowmap_vertex:ag,shadowmask_pars_fragment:og,skinbase_vertex:lg,skinning_pars_vertex:cg,skinning_vertex:hg,skinnormal_vertex:ug,specularmap_fragment:dg,specularmap_pars_fragment:fg,tonemapping_fragment:pg,tonemapping_pars_fragment:mg,transmission_fragment:gg,transmission_pars_fragment:_g,uv_pars_fragment:vg,uv_pars_vertex:xg,uv_vertex:yg,worldpos_vertex:bg,background_vert:Mg,background_frag:Sg,backgroundCube_vert:Eg,backgroundCube_frag:wg,cube_vert:Tg,cube_frag:Ag,depth_vert:Rg,depth_frag:Cg,distance_vert:Pg,distance_frag:Lg,equirect_vert:Dg,equirect_frag:Ig,linedashed_vert:Ng,linedashed_frag:Ug,meshbasic_vert:Og,meshbasic_frag:Fg,meshlambert_vert:kg,meshlambert_frag:Bg,meshmatcap_vert:zg,meshmatcap_frag:Hg,meshnormal_vert:Vg,meshnormal_frag:Gg,meshphong_vert:Wg,meshphong_frag:$g,meshphysical_vert:Xg,meshphysical_frag:qg,meshtoon_vert:Yg,meshtoon_frag:Zg,points_vert:Kg,points_frag:jg,shadow_vert:Jg,shadow_frag:Qg,sprite_vert:e_,sprite_frag:t_},pe={common:{diffuse:{value:new ye(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new Xe},alphaMap:{value:null},alphaMapTransform:{value:new Xe},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new Xe}},envmap:{envMap:{value:null},envMapRotation:{value:new Xe},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new Xe}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new Xe}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new Xe},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new Xe},normalScale:{value:new Fe(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new Xe},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new Xe}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new Xe}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new Xe}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new ye(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new P},probesMax:{value:new P},probesResolution:{value:new P}},points:{diffuse:{value:new ye(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new Xe},alphaTest:{value:0},uvTransform:{value:new Xe}},sprite:{diffuse:{value:new ye(16777215)},opacity:{value:1},center:{value:new Fe(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new Xe},alphaMap:{value:null},alphaMapTransform:{value:new Xe},alphaTest:{value:0}}},Ln={basic:{uniforms:Jt([pe.common,pe.specularmap,pe.envmap,pe.aomap,pe.lightmap,pe.fog]),vertexShader:Ze.meshbasic_vert,fragmentShader:Ze.meshbasic_frag},lambert:{uniforms:Jt([pe.common,pe.specularmap,pe.envmap,pe.aomap,pe.lightmap,pe.emissivemap,pe.bumpmap,pe.normalmap,pe.displacementmap,pe.fog,pe.lights,{emissive:{value:new ye(0)},envMapIntensity:{value:1}}]),vertexShader:Ze.meshlambert_vert,fragmentShader:Ze.meshlambert_frag},phong:{uniforms:Jt([pe.common,pe.specularmap,pe.envmap,pe.aomap,pe.lightmap,pe.emissivemap,pe.bumpmap,pe.normalmap,pe.displacementmap,pe.fog,pe.lights,{emissive:{value:new ye(0)},specular:{value:new ye(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:Ze.meshphong_vert,fragmentShader:Ze.meshphong_frag},standard:{uniforms:Jt([pe.common,pe.envmap,pe.aomap,pe.lightmap,pe.emissivemap,pe.bumpmap,pe.normalmap,pe.displacementmap,pe.roughnessmap,pe.metalnessmap,pe.fog,pe.lights,{emissive:{value:new ye(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:Ze.meshphysical_vert,fragmentShader:Ze.meshphysical_frag},toon:{uniforms:Jt([pe.common,pe.aomap,pe.lightmap,pe.emissivemap,pe.bumpmap,pe.normalmap,pe.displacementmap,pe.gradientmap,pe.fog,pe.lights,{emissive:{value:new ye(0)}}]),vertexShader:Ze.meshtoon_vert,fragmentShader:Ze.meshtoon_frag},matcap:{uniforms:Jt([pe.common,pe.bumpmap,pe.normalmap,pe.displacementmap,pe.fog,{matcap:{value:null}}]),vertexShader:Ze.meshmatcap_vert,fragmentShader:Ze.meshmatcap_frag},points:{uniforms:Jt([pe.points,pe.fog]),vertexShader:Ze.points_vert,fragmentShader:Ze.points_frag},dashed:{uniforms:Jt([pe.common,pe.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:Ze.linedashed_vert,fragmentShader:Ze.linedashed_frag},depth:{uniforms:Jt([pe.common,pe.displacementmap]),vertexShader:Ze.depth_vert,fragmentShader:Ze.depth_frag},normal:{uniforms:Jt([pe.common,pe.bumpmap,pe.normalmap,pe.displacementmap,{opacity:{value:1}}]),vertexShader:Ze.meshnormal_vert,fragmentShader:Ze.meshnormal_frag},sprite:{uniforms:Jt([pe.sprite,pe.fog]),vertexShader:Ze.sprite_vert,fragmentShader:Ze.sprite_frag},background:{uniforms:{uvTransform:{value:new Xe},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:Ze.background_vert,fragmentShader:Ze.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new Xe}},vertexShader:Ze.backgroundCube_vert,fragmentShader:Ze.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:Ze.cube_vert,fragmentShader:Ze.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:Ze.equirect_vert,fragmentShader:Ze.equirect_frag},distance:{uniforms:Jt([pe.common,pe.displacementmap,{referencePosition:{value:new P},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:Ze.distance_vert,fragmentShader:Ze.distance_frag},shadow:{uniforms:Jt([pe.lights,pe.fog,{color:{value:new ye(0)},opacity:{value:1}}]),vertexShader:Ze.shadow_vert,fragmentShader:Ze.shadow_frag}};Ln.physical={uniforms:Jt([Ln.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new Xe},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new Xe},clearcoatNormalScale:{value:new Fe(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new Xe},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new Xe},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new Xe},sheen:{value:0},sheenColor:{value:new ye(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new Xe},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new Xe},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new Xe},transmissionSamplerSize:{value:new Fe},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new Xe},attenuationDistance:{value:0},attenuationColor:{value:new ye(0)},specularColor:{value:new ye(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new Xe},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new Xe},anisotropyVector:{value:new Fe},anisotropyMap:{value:null},anisotropyMapTransform:{value:new Xe}}]),vertexShader:Ze.meshphysical_vert,fragmentShader:Ze.meshphysical_frag};const Hr={r:0,b:0,g:0},n_=new He,sd=new Xe;sd.set(-1,0,0,0,1,0,0,0,1);function i_(i,e,t,n,s,r){const a=new ye(0);let o=s===!0?0:1,l,c,h=null,d=0,u=null;function p(M){let E=M.isScene===!0?M.background:null;if(E&&E.isTexture){const y=M.backgroundBlurriness>0;E=e.get(E,y)}return E}function g(M){let E=!1;const y=p(M);y===null?m(a,o):y&&y.isColor&&(m(y,1),E=!0);const T=i.xr.getEnvironmentBlendMode();T==="additive"?t.buffers.color.setClear(0,0,0,1,r):T==="alpha-blend"&&t.buffers.color.setClear(0,0,0,0,r),(i.autoClear||E)&&(t.buffers.depth.setTest(!0),t.buffers.depth.setMask(!0),t.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function x(M,E){const y=p(E);y&&(y.isCubeTexture||y.mapping===ba)?(c===void 0&&(c=new ht(new Tt(1,1,1),new En({name:"BackgroundCubeMaterial",uniforms:Ss(Ln.backgroundCube.uniforms),vertexShader:Ln.backgroundCube.vertexShader,fragmentShader:Ln.backgroundCube.fragmentShader,side:rn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),c.geometry.deleteAttribute("uv"),c.onBeforeRender=function(T,S,R){this.matrixWorld.copyPosition(R.matrixWorld)},Object.defineProperty(c.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),n.update(c)),c.material.uniforms.envMap.value=y,c.material.uniforms.backgroundBlurriness.value=E.backgroundBlurriness,c.material.uniforms.backgroundIntensity.value=E.backgroundIntensity,c.material.uniforms.backgroundRotation.value.setFromMatrix4(n_.makeRotationFromEuler(E.backgroundRotation)).transpose(),y.isCubeTexture&&y.isRenderTargetTexture===!1&&c.material.uniforms.backgroundRotation.value.premultiply(sd),c.material.toneMapped=et.getTransfer(y.colorSpace)!==ft,(h!==y||d!==y.version||u!==i.toneMapping)&&(c.material.needsUpdate=!0,h=y,d=y.version,u=i.toneMapping),c.layers.enableAll(),M.unshift(c,c.geometry,c.material,0,0,null)):y&&y.isTexture&&(l===void 0&&(l=new ht(new un(2,2),new En({name:"BackgroundMaterial",uniforms:Ss(Ln.background.uniforms),vertexShader:Ln.background.vertexShader,fragmentShader:Ln.background.fragmentShader,side:vi,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),n.update(l)),l.material.uniforms.t2D.value=y,l.material.uniforms.backgroundIntensity.value=E.backgroundIntensity,l.material.toneMapped=et.getTransfer(y.colorSpace)!==ft,y.matrixAutoUpdate===!0&&y.updateMatrix(),l.material.uniforms.uvTransform.value.copy(y.matrix),(h!==y||d!==y.version||u!==i.toneMapping)&&(l.material.needsUpdate=!0,h=y,d=y.version,u=i.toneMapping),l.layers.enableAll(),M.unshift(l,l.geometry,l.material,0,0,null))}function m(M,E){M.getRGB(Hr,Qu(i)),t.buffers.color.setClear(Hr.r,Hr.g,Hr.b,E,r)}function f(){c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return a},setClearColor:function(M,E=1){a.set(M),o=E,m(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(M){o=M,m(a,o)},render:g,addToRenderList:x,dispose:f}}function s_(i,e){const t=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},s=u(null);let r=s,a=!1;function o(L,N,V,$,F){let W=!1;const G=d(L,$,V,N);r!==G&&(r=G,c(r.object)),W=p(L,$,V,F),W&&g(L,$,V,F),F!==null&&e.update(F,i.ELEMENT_ARRAY_BUFFER),(W||a)&&(a=!1,y(L,N,V,$),F!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,e.get(F).buffer))}function l(){return i.createVertexArray()}function c(L){return i.bindVertexArray(L)}function h(L){return i.deleteVertexArray(L)}function d(L,N,V,$){const F=$.wireframe===!0;let W=n[N.id];W===void 0&&(W={},n[N.id]=W);const G=L.isInstancedMesh===!0?L.id:0;let J=W[G];J===void 0&&(J={},W[G]=J);let te=J[V.id];te===void 0&&(te={},J[V.id]=te);let oe=te[F];return oe===void 0&&(oe=u(l()),te[F]=oe),oe}function u(L){const N=[],V=[],$=[];for(let F=0;F<t;F++)N[F]=0,V[F]=0,$[F]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:N,enabledAttributes:V,attributeDivisors:$,object:L,attributes:{},index:null}}function p(L,N,V,$){const F=r.attributes,W=N.attributes;let G=0;const J=V.getAttributes();for(const te in J)if(J[te].location>=0){const me=F[te];let be=W[te];if(be===void 0&&(te==="instanceMatrix"&&L.instanceMatrix&&(be=L.instanceMatrix),te==="instanceColor"&&L.instanceColor&&(be=L.instanceColor)),me===void 0||me.attribute!==be||be&&me.data!==be.data)return!0;G++}return r.attributesNum!==G||r.index!==$}function g(L,N,V,$){const F={},W=N.attributes;let G=0;const J=V.getAttributes();for(const te in J)if(J[te].location>=0){let me=W[te];me===void 0&&(te==="instanceMatrix"&&L.instanceMatrix&&(me=L.instanceMatrix),te==="instanceColor"&&L.instanceColor&&(me=L.instanceColor));const be={};be.attribute=me,me&&me.data&&(be.data=me.data),F[te]=be,G++}r.attributes=F,r.attributesNum=G,r.index=$}function x(){const L=r.newAttributes;for(let N=0,V=L.length;N<V;N++)L[N]=0}function m(L){f(L,0)}function f(L,N){const V=r.newAttributes,$=r.enabledAttributes,F=r.attributeDivisors;V[L]=1,$[L]===0&&(i.enableVertexAttribArray(L),$[L]=1),F[L]!==N&&(i.vertexAttribDivisor(L,N),F[L]=N)}function M(){const L=r.newAttributes,N=r.enabledAttributes;for(let V=0,$=N.length;V<$;V++)N[V]!==L[V]&&(i.disableVertexAttribArray(V),N[V]=0)}function E(L,N,V,$,F,W,G){G===!0?i.vertexAttribIPointer(L,N,V,F,W):i.vertexAttribPointer(L,N,V,$,F,W)}function y(L,N,V,$){x();const F=$.attributes,W=V.getAttributes(),G=N.defaultAttributeValues;for(const J in W){const te=W[J];if(te.location>=0){let oe=F[J];if(oe===void 0&&(J==="instanceMatrix"&&L.instanceMatrix&&(oe=L.instanceMatrix),J==="instanceColor"&&L.instanceColor&&(oe=L.instanceColor)),oe!==void 0){const me=oe.normalized,be=oe.itemSize,at=e.get(oe);if(at===void 0)continue;const gt=at.buffer,it=at.type,Y=at.bytesPerElement,ae=it===i.INT||it===i.UNSIGNED_INT||oe.gpuType===Ll;if(oe.isInterleavedBufferAttribute){const ne=oe.data,Oe=ne.stride,Ve=oe.offset;if(ne.isInstancedInterleavedBuffer){for(let Ie=0;Ie<te.locationSize;Ie++)f(te.location+Ie,ne.meshPerAttribute);L.isInstancedMesh!==!0&&$._maxInstanceCount===void 0&&($._maxInstanceCount=ne.meshPerAttribute*ne.count)}else for(let Ie=0;Ie<te.locationSize;Ie++)m(te.location+Ie);i.bindBuffer(i.ARRAY_BUFFER,gt);for(let Ie=0;Ie<te.locationSize;Ie++)E(te.location+Ie,be/te.locationSize,it,me,Oe*Y,(Ve+be/te.locationSize*Ie)*Y,ae)}else{if(oe.isInstancedBufferAttribute){for(let ne=0;ne<te.locationSize;ne++)f(te.location+ne,oe.meshPerAttribute);L.isInstancedMesh!==!0&&$._maxInstanceCount===void 0&&($._maxInstanceCount=oe.meshPerAttribute*oe.count)}else for(let ne=0;ne<te.locationSize;ne++)m(te.location+ne);i.bindBuffer(i.ARRAY_BUFFER,gt);for(let ne=0;ne<te.locationSize;ne++)E(te.location+ne,be/te.locationSize,it,me,be*Y,be/te.locationSize*ne*Y,ae)}}else if(G!==void 0){const me=G[J];if(me!==void 0)switch(me.length){case 2:i.vertexAttrib2fv(te.location,me);break;case 3:i.vertexAttrib3fv(te.location,me);break;case 4:i.vertexAttrib4fv(te.location,me);break;default:i.vertexAttrib1fv(te.location,me)}}}}M()}function T(){w();for(const L in n){const N=n[L];for(const V in N){const $=N[V];for(const F in $){const W=$[F];for(const G in W)h(W[G].object),delete W[G];delete $[F]}}delete n[L]}}function S(L){if(n[L.id]===void 0)return;const N=n[L.id];for(const V in N){const $=N[V];for(const F in $){const W=$[F];for(const G in W)h(W[G].object),delete W[G];delete $[F]}}delete n[L.id]}function R(L){for(const N in n){const V=n[N];for(const $ in V){const F=V[$];if(F[L.id]===void 0)continue;const W=F[L.id];for(const G in W)h(W[G].object),delete W[G];delete F[L.id]}}}function v(L){for(const N in n){const V=n[N],$=L.isInstancedMesh===!0?L.id:0,F=V[$];if(F!==void 0){for(const W in F){const G=F[W];for(const J in G)h(G[J].object),delete G[J];delete F[W]}delete V[$],Object.keys(V).length===0&&delete n[N]}}}function w(){C(),a=!0,r!==s&&(r=s,c(r.object))}function C(){s.geometry=null,s.program=null,s.wireframe=!1}return{setup:o,reset:w,resetDefaultState:C,dispose:T,releaseStatesOfGeometry:S,releaseStatesOfObject:v,releaseStatesOfProgram:R,initAttributes:x,enableAttribute:m,disableUnusedAttributes:M}}function r_(i,e,t){let n;function s(l){n=l}function r(l,c){i.drawArrays(n,l,c),t.update(c,n,1)}function a(l,c,h){h!==0&&(i.drawArraysInstanced(n,l,c,h),t.update(c,n,h))}function o(l,c,h){if(h===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,l,0,c,0,h);let u=0;for(let p=0;p<h;p++)u+=c[p];t.update(u,n,1)}this.setMode=s,this.render=r,this.renderInstances=a,this.renderMultiDraw=o}function a_(i,e,t,n){let s;function r(){if(s!==void 0)return s;if(e.has("EXT_texture_filter_anisotropic")===!0){const R=e.get("EXT_texture_filter_anisotropic");s=i.getParameter(R.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else s=0;return s}function a(R){return!(R!==gn&&n.convert(R)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(R){const v=R===Kn&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(R!==hn&&n.convert(R)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE)&&R!==bn&&!v)}function l(R){if(R==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";R="mediump"}return R==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp";const h=l(c);h!==c&&(ke("WebGLRenderer:",c,"not supported, using",h,"instead."),c=h);const d=t.logarithmicDepthBuffer===!0,u=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control");t.reversedDepthBuffer===!0&&u===!1&&ke("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");const p=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),g=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),x=i.getParameter(i.MAX_TEXTURE_SIZE),m=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),f=i.getParameter(i.MAX_VERTEX_ATTRIBS),M=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),E=i.getParameter(i.MAX_VARYING_VECTORS),y=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),T=i.getParameter(i.MAX_SAMPLES),S=i.getParameter(i.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:r,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:d,reversedDepthBuffer:u,maxTextures:p,maxVertexTextures:g,maxTextureSize:x,maxCubemapSize:m,maxAttributes:f,maxVertexUniforms:M,maxVaryings:E,maxFragmentUniforms:y,maxSamples:T,samples:S}}function o_(i){const e=this;let t=null,n=0,s=!1,r=!1;const a=new ui,o=new Xe,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(d,u){const p=d.length!==0||u||n!==0||s;return s=u,n=d.length,p},this.beginShadows=function(){r=!0,h(null)},this.endShadows=function(){r=!1},this.setGlobalState=function(d,u){t=h(d,u,0)},this.setState=function(d,u,p){const g=d.clippingPlanes,x=d.clipIntersection,m=d.clipShadows,f=i.get(d);if(!s||g===null||g.length===0||r&&!m)r?h(null):c();else{const M=r?0:n,E=M*4;let y=f.clippingState||null;l.value=y,y=h(g,u,E,p);for(let T=0;T!==E;++T)y[T]=t[T];f.clippingState=y,this.numIntersection=x?this.numPlanes:0,this.numPlanes+=M}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=n>0),e.numPlanes=n,e.numIntersection=0}function h(d,u,p,g){const x=d!==null?d.length:0;let m=null;if(x!==0){if(m=l.value,g!==!0||m===null){const f=p+x*4,M=u.matrixWorldInverse;o.getNormalMatrix(M),(m===null||m.length<f)&&(m=new Float32Array(f));for(let E=0,y=p;E!==x;++E,y+=4)a.copy(d[E]).applyMatrix4(M,o),a.normal.toArray(m,y),m[y+3]=a.constant}l.value=m,l.needsUpdate=!0}return e.numPlanes=x,e.numIntersection=0,m}}const fi=4,nh=[.125,.215,.35,.446,.526,.582],Ni=20,l_=256,Ws=new ql,ih=new ye;let so=null,ro=0,ao=0,oo=!1;const c_=new P;class sh{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._sigmas=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,n=.1,s=100,r={}){const{size:a=256,position:o=c_}=r;so=this._renderer.getRenderTarget(),ro=this._renderer.getActiveCubeFace(),ao=this._renderer.getActiveMipmapLevel(),oo=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);const l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,n,s,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=oh(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=ah(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(so,ro,ao),this._renderer.xr.enabled=oo,e.scissorTest=!1,ss(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Fi||e.mapping===bs?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),so=this._renderer.getRenderTarget(),ro=this._renderer.getActiveCubeFace(),ao=this._renderer.getActiveMipmapLevel(),oo=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const n=t||this._allocateTargets();return this._textureToCubeUV(e,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,n={magFilter:Zt,minFilter:Zt,generateMipmaps:!1,type:Kn,format:gn,colorSpace:oa,depthBuffer:!1},s=rh(e,t,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=rh(e,t,n);const{_lodMax:r}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods,sigmas:this._sigmas}=h_(r)),this._blurMaterial=d_(r,e,t),this._ggxMaterial=u_(r,e,t)}return s}_compileMaterial(e){const t=new ht(new jt,e);this._renderer.compile(t,Ws)}_sceneToCubeUV(e,t,n,s,r){const l=new cn(90,1,t,n),c=[1,-1,1,1,1,1],h=[1,1,1,-1,-1,-1],d=this._renderer,u=d.autoClear,p=d.toneMapping;d.getClearColor(ih),d.toneMapping=In,d.autoClear=!1,d.state.buffers.depth.getReversed()&&(d.setRenderTarget(s),d.clearDepth(),d.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new ht(new Tt,new ct({name:"PMREM.Background",side:rn,depthWrite:!1,depthTest:!1})));const x=this._backgroundBox,m=x.material;let f=!1;const M=e.background;M?M.isColor&&(m.color.copy(M),e.background=null,f=!0):(m.color.copy(ih),f=!0);for(let E=0;E<6;E++){const y=E%3;y===0?(l.up.set(0,c[E],0),l.position.set(r.x,r.y,r.z),l.lookAt(r.x+h[E],r.y,r.z)):y===1?(l.up.set(0,0,c[E]),l.position.set(r.x,r.y,r.z),l.lookAt(r.x,r.y+h[E],r.z)):(l.up.set(0,c[E],0),l.position.set(r.x,r.y,r.z),l.lookAt(r.x,r.y,r.z+h[E]));const T=this._cubeSize;ss(s,y*T,E>2?T:0,T,T),d.setRenderTarget(s),f&&d.render(x,l),d.render(e,l)}d.toneMapping=p,d.autoClear=u,e.background=M}_textureToCubeUV(e,t){const n=this._renderer,s=e.mapping===Fi||e.mapping===bs;s?(this._cubemapMaterial===null&&(this._cubemapMaterial=oh()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=ah());const r=s?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=r;const o=r.uniforms;o.envMap.value=e;const l=this._cubeSize;ss(t,0,0,3*l,2*l),n.setRenderTarget(t),n.render(a,Ws)}_applyPMREM(e){const t=this._renderer,n=t.autoClear;t.autoClear=!1;const s=this._lodMeshes.length;for(let r=1;r<s;r++)this._applyGGXFilter(e,r-1,r);t.autoClear=n}_applyGGXFilter(e,t,n){const s=this._renderer,r=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[n];o.material=a;const l=a.uniforms,c=n/(this._lodMeshes.length-1),h=t/(this._lodMeshes.length-1),d=Math.sqrt(c*c-h*h),u=0+c*1.25,p=d*u,{_lodMax:g}=this,x=this._sizeLods[n],m=3*x*(n>g-fi?n-g+fi:0),f=4*(this._cubeSize-x);l.envMap.value=e.texture,l.roughness.value=p,l.mipInt.value=g-t,ss(r,m,f,3*x,2*x),s.setRenderTarget(r),s.render(o,Ws),l.envMap.value=r.texture,l.roughness.value=0,l.mipInt.value=g-n,ss(e,m,f,3*x,2*x),s.setRenderTarget(e),s.render(o,Ws)}_blur(e,t,n,s,r){const a=this._pingPongRenderTarget;this._halfBlur(e,a,t,n,s,"latitudinal",r),this._halfBlur(a,e,n,n,s,"longitudinal",r)}_halfBlur(e,t,n,s,r,a,o){const l=this._renderer,c=this._blurMaterial;a!=="latitudinal"&&a!=="longitudinal"&&st("blur direction must be either latitudinal or longitudinal!");const h=3,d=this._lodMeshes[s];d.material=c;const u=c.uniforms,p=this._sizeLods[n]-1,g=isFinite(r)?Math.PI/(2*p):2*Math.PI/(2*Ni-1),x=r/g,m=isFinite(r)?1+Math.floor(h*x):Ni;m>Ni&&ke(`sigmaRadians, ${r}, is too large and will clip, as it requested ${m} samples when the maximum is set to ${Ni}`);const f=[];let M=0;for(let R=0;R<Ni;++R){const v=R/x,w=Math.exp(-v*v/2);f.push(w),R===0?M+=w:R<m&&(M+=2*w)}for(let R=0;R<f.length;R++)f[R]=f[R]/M;u.envMap.value=e.texture,u.samples.value=m,u.weights.value=f,u.latitudinal.value=a==="latitudinal",o&&(u.poleAxis.value=o);const{_lodMax:E}=this;u.dTheta.value=g,u.mipInt.value=E-n;const y=this._sizeLods[s],T=3*y*(s>E-fi?s-E+fi:0),S=4*(this._cubeSize-y);ss(t,T,S,3*y,2*y),l.setRenderTarget(t),l.render(d,Ws)}}function h_(i){const e=[],t=[],n=[];let s=i;const r=i-fi+1+nh.length;for(let a=0;a<r;a++){const o=Math.pow(2,s);e.push(o);let l=1/o;a>i-fi?l=nh[a-i+fi-1]:a===0&&(l=0),t.push(l);const c=1/(o-2),h=-c,d=1+c,u=[h,h,d,h,d,d,h,h,d,d,h,d],p=6,g=6,x=3,m=2,f=1,M=new Float32Array(x*g*p),E=new Float32Array(m*g*p),y=new Float32Array(f*g*p);for(let S=0;S<p;S++){const R=S%3*2/3-1,v=S>2?0:-1,w=[R,v,0,R+2/3,v,0,R+2/3,v+1,0,R,v,0,R+2/3,v+1,0,R,v+1,0];M.set(w,x*g*S),E.set(u,m*g*S);const C=[S,S,S,S,S,S];y.set(C,f*g*S)}const T=new jt;T.setAttribute("position",new Mn(M,x)),T.setAttribute("uv",new Mn(E,m)),T.setAttribute("faceIndex",new Mn(y,f)),n.push(new ht(T,null)),s>fi&&s--}return{lodMeshes:n,sizeLods:e,sigmas:t}}function rh(i,e,t){const n=new Nn(i,e,t);return n.texture.mapping=ba,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function ss(i,e,t,n,s){i.viewport.set(e,t,n,s),i.scissor.set(e,t,n,s)}function u_(i,e,t){return new En({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:l_,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Sa(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float roughness;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359

			// Van der Corput radical inverse
			float radicalInverse_VdC(uint bits) {
				bits = (bits << 16u) | (bits >> 16u);
				bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
				bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
				bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
				bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
				return float(bits) * 2.3283064365386963e-10; // / 0x100000000
			}

			// Hammersley sequence
			vec2 hammersley(uint i, uint N) {
				return vec2(float(i) / float(N), radicalInverse_VdC(i));
			}

			// GGX VNDF importance sampling (Eric Heitz 2018)
			// "Sampling the GGX Distribution of Visible Normals"
			// https://jcgt.org/published/0007/04/01/
			vec3 importanceSampleGGX_VNDF(vec2 Xi, vec3 V, float roughness) {
				float alpha = roughness * roughness;

				// Section 4.1: Orthonormal basis
				vec3 T1 = vec3(1.0, 0.0, 0.0);
				vec3 T2 = cross(V, T1);

				// Section 4.2: Parameterization of projected area
				float r = sqrt(Xi.x);
				float phi = 2.0 * PI * Xi.y;
				float t1 = r * cos(phi);
				float t2 = r * sin(phi);
				float s = 0.5 * (1.0 + V.z);
				t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;

				// Section 4.3: Reprojection onto hemisphere
				vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0.0, 1.0 - t1 * t1 - t2 * t2)) * V;

				// Section 3.4: Transform back to ellipsoid configuration
				return normalize(vec3(alpha * Nh.x, alpha * Nh.y, max(0.0, Nh.z)));
			}

			void main() {
				vec3 N = normalize(vOutputDirection);
				vec3 V = N; // Assume view direction equals normal for pre-filtering

				vec3 prefilteredColor = vec3(0.0);
				float totalWeight = 0.0;

				// For very low roughness, just sample the environment directly
				if (roughness < 0.001) {
					gl_FragColor = vec4(bilinearCubeUV(envMap, N, mipInt), 1.0);
					return;
				}

				// Tangent space basis for VNDF sampling
				vec3 up = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
				vec3 tangent = normalize(cross(up, N));
				vec3 bitangent = cross(N, tangent);

				for(uint i = 0u; i < uint(GGX_SAMPLES); i++) {
					vec2 Xi = hammersley(i, uint(GGX_SAMPLES));

					// For PMREM, V = N, so in tangent space V is always (0, 0, 1)
					vec3 H_tangent = importanceSampleGGX_VNDF(Xi, vec3(0.0, 0.0, 1.0), roughness);

					// Transform H back to world space
					vec3 H = normalize(tangent * H_tangent.x + bitangent * H_tangent.y + N * H_tangent.z);
					vec3 L = normalize(2.0 * dot(V, H) * H - V);

					float NdotL = max(dot(N, L), 0.0);

					if(NdotL > 0.0) {
						// Sample environment at fixed mip level
						// VNDF importance sampling handles the distribution filtering
						vec3 sampleColor = bilinearCubeUV(envMap, L, mipInt);

						// Weight by NdotL for the split-sum approximation
						// VNDF PDF naturally accounts for the visible microfacet distribution
						prefilteredColor += sampleColor * NdotL;
						totalWeight += NdotL;
					}
				}

				if (totalWeight > 0.0) {
					prefilteredColor = prefilteredColor / totalWeight;
				}

				gl_FragColor = vec4(prefilteredColor, 1.0);
			}
		`,blending:Yn,depthTest:!1,depthWrite:!1})}function d_(i,e,t){const n=new Float32Array(Ni),s=new P(0,1,0);return new En({name:"SphericalGaussianBlur",defines:{n:Ni,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:n},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:s}},vertexShader:Sa(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:Yn,depthTest:!1,depthWrite:!1})}function ah(){return new En({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Sa(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:Yn,depthTest:!1,depthWrite:!1})}function oh(){return new En({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Sa(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Yn,depthTest:!1,depthWrite:!1})}function Sa(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}class rd extends Nn{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;const n={width:e,height:e,depth:1},s=[n,n,n,n,n,n];this.texture=new Zu(s),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;const n={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},s=new Tt(5,5,5),r=new En({name:"CubemapFromEquirect",uniforms:Ss(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:rn,blending:Yn});r.uniforms.tEquirect.value=t;const a=new ht(s,r),o=t.minFilter;return t.minFilter===$n&&(t.minFilter=Zt),new gp(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,n=!0,s=!0){const r=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,n,s);e.setRenderTarget(r)}}function f_(i){let e=new WeakMap,t=new WeakMap,n=null;function s(u,p=!1){return u==null?null:p?a(u):r(u)}function r(u){if(u&&u.isTexture){const p=u.mapping;if(p===Ca||p===Pa)if(e.has(u)){const g=e.get(u).texture;return o(g,u.mapping)}else{const g=u.image;if(g&&g.height>0){const x=new rd(g.height);return x.fromEquirectangularTexture(i,u),e.set(u,x),u.addEventListener("dispose",c),o(x.texture,u.mapping)}else return null}}return u}function a(u){if(u&&u.isTexture){const p=u.mapping,g=p===Ca||p===Pa,x=p===Fi||p===bs;if(g||x){let m=t.get(u);const f=m!==void 0?m.texture.pmremVersion:0;if(u.isRenderTargetTexture&&u.pmremVersion!==f)return n===null&&(n=new sh(i)),m=g?n.fromEquirectangular(u,m):n.fromCubemap(u,m),m.texture.pmremVersion=u.pmremVersion,t.set(u,m),m.texture;if(m!==void 0)return m.texture;{const M=u.image;return g&&M&&M.height>0||x&&M&&l(M)?(n===null&&(n=new sh(i)),m=g?n.fromEquirectangular(u):n.fromCubemap(u),m.texture.pmremVersion=u.pmremVersion,t.set(u,m),u.addEventListener("dispose",h),m.texture):null}}}return u}function o(u,p){return p===Ca?u.mapping=Fi:p===Pa&&(u.mapping=bs),u}function l(u){let p=0;const g=6;for(let x=0;x<g;x++)u[x]!==void 0&&p++;return p===g}function c(u){const p=u.target;p.removeEventListener("dispose",c);const g=e.get(p);g!==void 0&&(e.delete(p),g.dispose())}function h(u){const p=u.target;p.removeEventListener("dispose",h);const g=t.get(p);g!==void 0&&(t.delete(p),g.dispose())}function d(){e=new WeakMap,t=new WeakMap,n!==null&&(n.dispose(),n=null)}return{get:s,dispose:d}}function p_(i){const e={};function t(n){if(e[n]!==void 0)return e[n];const s=i.getExtension(n);return e[n]=s,s}return{has:function(n){return t(n)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(n){const s=t(n);return s===null&&gs("WebGLRenderer: "+n+" extension not supported."),s}}}function m_(i,e,t,n){const s={},r=new WeakMap;function a(d){const u=d.target;u.index!==null&&e.remove(u.index);for(const g in u.attributes)e.remove(u.attributes[g]);u.removeEventListener("dispose",a),delete s[u.id];const p=r.get(u);p&&(e.remove(p),r.delete(u)),n.releaseStatesOfGeometry(u),u.isInstancedBufferGeometry===!0&&delete u._maxInstanceCount,t.memory.geometries--}function o(d,u){return s[u.id]===!0||(u.addEventListener("dispose",a),s[u.id]=!0,t.memory.geometries++),u}function l(d){const u=d.attributes;for(const p in u)e.update(u[p],i.ARRAY_BUFFER)}function c(d){const u=[],p=d.index,g=d.attributes.position;let x=0;if(g===void 0)return;if(p!==null){const M=p.array;x=p.version;for(let E=0,y=M.length;E<y;E+=3){const T=M[E+0],S=M[E+1],R=M[E+2];u.push(T,S,S,R,R,T)}}else{const M=g.array;x=g.version;for(let E=0,y=M.length/3-1;E<y;E+=3){const T=E+0,S=E+1,R=E+2;u.push(T,S,S,R,R,T)}}const m=new(g.count>=65535?qu:Xu)(u,1);m.version=x;const f=r.get(d);f&&e.remove(f),r.set(d,m)}function h(d){const u=r.get(d);if(u){const p=d.index;p!==null&&u.version<p.version&&c(d)}else c(d);return r.get(d)}return{get:o,update:l,getWireframeAttribute:h}}function g_(i,e,t){let n;function s(d){n=d}let r,a;function o(d){r=d.type,a=d.bytesPerElement}function l(d,u){i.drawElements(n,u,r,d*a),t.update(u,n,1)}function c(d,u,p){p!==0&&(i.drawElementsInstanced(n,u,r,d*a,p),t.update(u,n,p))}function h(d,u,p){if(p===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,u,0,r,d,0,p);let x=0;for(let m=0;m<p;m++)x+=u[m];t.update(x,n,1)}this.setMode=s,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=h}function __(i){const e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function n(r,a,o){switch(t.calls++,a){case i.TRIANGLES:t.triangles+=o*(r/3);break;case i.LINES:t.lines+=o*(r/2);break;case i.LINE_STRIP:t.lines+=o*(r-1);break;case i.LINE_LOOP:t.lines+=o*r;break;case i.POINTS:t.points+=o*r;break;default:st("WebGLInfo: Unknown draw mode:",a);break}}function s(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:s,update:n}}function v_(i,e,t){const n=new WeakMap,s=new At;function r(a,o,l){const c=a.morphTargetInfluences,h=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,d=h!==void 0?h.length:0;let u=n.get(o);if(u===void 0||u.count!==d){let w=function(){R.dispose(),n.delete(o),o.removeEventListener("dispose",w)};u!==void 0&&u.texture.dispose();const p=o.morphAttributes.position!==void 0,g=o.morphAttributes.normal!==void 0,x=o.morphAttributes.color!==void 0,m=o.morphAttributes.position||[],f=o.morphAttributes.normal||[],M=o.morphAttributes.color||[];let E=0;p===!0&&(E=1),g===!0&&(E=2),x===!0&&(E=3);let y=o.attributes.position.count*E,T=1;y>e.maxTextureSize&&(T=Math.ceil(y/e.maxTextureSize),y=e.maxTextureSize);const S=new Float32Array(y*T*4*d),R=new Wu(S,y,T,d);R.type=bn,R.needsUpdate=!0;const v=E*4;for(let C=0;C<d;C++){const L=m[C],N=f[C],V=M[C],$=y*T*4*C;for(let F=0;F<L.count;F++){const W=F*v;p===!0&&(s.fromBufferAttribute(L,F),S[$+W+0]=s.x,S[$+W+1]=s.y,S[$+W+2]=s.z,S[$+W+3]=0),g===!0&&(s.fromBufferAttribute(N,F),S[$+W+4]=s.x,S[$+W+5]=s.y,S[$+W+6]=s.z,S[$+W+7]=0),x===!0&&(s.fromBufferAttribute(V,F),S[$+W+8]=s.x,S[$+W+9]=s.y,S[$+W+10]=s.z,S[$+W+11]=V.itemSize===4?s.w:1)}}u={count:d,texture:R,size:new Fe(y,T)},n.set(o,u),o.addEventListener("dispose",w)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(i,"morphTexture",a.morphTexture,t);else{let p=0;for(let x=0;x<c.length;x++)p+=c[x];const g=o.morphTargetsRelative?1:1-p;l.getUniforms().setValue(i,"morphTargetBaseInfluence",g),l.getUniforms().setValue(i,"morphTargetInfluences",c)}l.getUniforms().setValue(i,"morphTargetsTexture",u.texture,t),l.getUniforms().setValue(i,"morphTargetsTextureSize",u.size)}return{update:r}}function x_(i,e,t,n,s){let r=new WeakMap;function a(c){const h=s.render.frame,d=c.geometry,u=e.get(c,d);if(r.get(u)!==h&&(e.update(u),r.set(u,h)),c.isInstancedMesh&&(c.hasEventListener("dispose",l)===!1&&c.addEventListener("dispose",l),r.get(c)!==h&&(t.update(c.instanceMatrix,i.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,i.ARRAY_BUFFER),r.set(c,h))),c.isSkinnedMesh){const p=c.skeleton;r.get(p)!==h&&(p.update(),r.set(p,h))}return u}function o(){r=new WeakMap}function l(c){const h=c.target;h.removeEventListener("dispose",l),n.releaseStatesOfObject(h),t.remove(h.instanceMatrix),h.instanceColor!==null&&t.remove(h.instanceColor)}return{update:a,dispose:o}}const y_={[Cu]:"LINEAR_TONE_MAPPING",[Pu]:"REINHARD_TONE_MAPPING",[Lu]:"CINEON_TONE_MAPPING",[Du]:"ACES_FILMIC_TONE_MAPPING",[Nu]:"AGX_TONE_MAPPING",[Uu]:"NEUTRAL_TONE_MAPPING",[Iu]:"CUSTOM_TONE_MAPPING"};function b_(i,e,t,n,s,r){const a=new Nn(e,t,{type:i,depthBuffer:s,stencilBuffer:r,samples:n?4:0,depthTexture:s?new Ms(e,t):void 0}),o=new Nn(e,t,{type:Kn,depthBuffer:!1,stencilBuffer:!1}),l=new jt;l.setAttribute("position",new St([-1,3,0,-1,-1,0,3,-1,0],3)),l.setAttribute("uv",new St([0,2,0,0,2,0],2));const c=new lp({uniforms:{tDiffuse:{value:null}},vertexShader:`
			precision highp float;

			uniform mat4 modelViewMatrix;
			uniform mat4 projectionMatrix;

			attribute vec3 position;
			attribute vec2 uv;

			varying vec2 vUv;

			void main() {
				vUv = uv;
				gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
			}`,fragmentShader:`
			precision highp float;

			uniform sampler2D tDiffuse;

			varying vec2 vUv;

			#include <tonemapping_pars_fragment>
			#include <colorspace_pars_fragment>

			void main() {
				gl_FragColor = texture2D( tDiffuse, vUv );

				#ifdef LINEAR_TONE_MAPPING
					gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );
				#elif defined( REINHARD_TONE_MAPPING )
					gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );
				#elif defined( CINEON_TONE_MAPPING )
					gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );
				#elif defined( ACES_FILMIC_TONE_MAPPING )
					gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );
				#elif defined( AGX_TONE_MAPPING )
					gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );
				#elif defined( NEUTRAL_TONE_MAPPING )
					gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );
				#elif defined( CUSTOM_TONE_MAPPING )
					gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );
				#endif

				#ifdef SRGB_TRANSFER
					gl_FragColor = sRGBTransferOETF( gl_FragColor );
				#endif
			}`,depthTest:!1,depthWrite:!1}),h=new ht(l,c),d=new ql(-1,1,1,-1,0,1);let u=null,p=null,g=!1,x,m=null,f=[],M=!1;this.setSize=function(E,y){a.setSize(E,y),o.setSize(E,y);for(let T=0;T<f.length;T++){const S=f[T];S.setSize&&S.setSize(E,y)}},this.setEffects=function(E){f=E,M=f.length>0&&f[0].isRenderPass===!0;const y=a.width,T=a.height;for(let S=0;S<f.length;S++){const R=f[S];R.setSize&&R.setSize(y,T)}},this.begin=function(E,y){if(g||E.toneMapping===In&&f.length===0)return!1;if(m=y,y!==null){const T=y.width,S=y.height;(a.width!==T||a.height!==S)&&this.setSize(T,S)}return M===!1&&E.setRenderTarget(a),x=E.toneMapping,E.toneMapping=In,!0},this.hasRenderPass=function(){return M},this.end=function(E,y){E.toneMapping=x,g=!0;let T=a,S=o;for(let R=0;R<f.length;R++){const v=f[R];if(v.enabled!==!1&&(v.render(E,S,T,y),v.needsSwap!==!1)){const w=T;T=S,S=w}}if(u!==E.outputColorSpace||p!==E.toneMapping){u=E.outputColorSpace,p=E.toneMapping,c.defines={},et.getTransfer(u)===ft&&(c.defines.SRGB_TRANSFER="");const R=y_[p];R&&(c.defines[R]=""),c.needsUpdate=!0}c.uniforms.tDiffuse.value=T.texture,E.setRenderTarget(m),E.render(h,d),m=null,g=!1},this.isCompositing=function(){return g},this.dispose=function(){a.depthTexture&&a.depthTexture.dispose(),a.dispose(),o.dispose(),l.dispose(),c.dispose()}}const ad=new Kt,pl=new Ms(1,1),od=new Wu,ld=new kf,cd=new Zu,lh=[],ch=[],hh=new Float32Array(16),uh=new Float32Array(9),dh=new Float32Array(4);function Ns(i,e,t){const n=i[0];if(n<=0||n>0)return i;const s=e*t;let r=lh[s];if(r===void 0&&(r=new Float32Array(s),lh[s]=r),e!==0){n.toArray(r,0);for(let a=1,o=0;a!==e;++a)o+=t,i[a].toArray(r,o)}return r}function zt(i,e){if(i.length!==e.length)return!1;for(let t=0,n=i.length;t<n;t++)if(i[t]!==e[t])return!1;return!0}function Ht(i,e){for(let t=0,n=e.length;t<n;t++)i[t]=e[t]}function Ea(i,e){let t=ch[e];t===void 0&&(t=new Int32Array(e),ch[e]=t);for(let n=0;n!==e;++n)t[n]=i.allocateTextureUnit();return t}function M_(i,e){const t=this.cache;t[0]!==e&&(i.uniform1f(this.addr,e),t[0]=e)}function S_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(zt(t,e))return;i.uniform2fv(this.addr,e),Ht(t,e)}}function E_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(i.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(zt(t,e))return;i.uniform3fv(this.addr,e),Ht(t,e)}}function w_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(zt(t,e))return;i.uniform4fv(this.addr,e),Ht(t,e)}}function T_(i,e){const t=this.cache,n=e.elements;if(n===void 0){if(zt(t,e))return;i.uniformMatrix2fv(this.addr,!1,e),Ht(t,e)}else{if(zt(t,n))return;dh.set(n),i.uniformMatrix2fv(this.addr,!1,dh),Ht(t,n)}}function A_(i,e){const t=this.cache,n=e.elements;if(n===void 0){if(zt(t,e))return;i.uniformMatrix3fv(this.addr,!1,e),Ht(t,e)}else{if(zt(t,n))return;uh.set(n),i.uniformMatrix3fv(this.addr,!1,uh),Ht(t,n)}}function R_(i,e){const t=this.cache,n=e.elements;if(n===void 0){if(zt(t,e))return;i.uniformMatrix4fv(this.addr,!1,e),Ht(t,e)}else{if(zt(t,n))return;hh.set(n),i.uniformMatrix4fv(this.addr,!1,hh),Ht(t,n)}}function C_(i,e){const t=this.cache;t[0]!==e&&(i.uniform1i(this.addr,e),t[0]=e)}function P_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(zt(t,e))return;i.uniform2iv(this.addr,e),Ht(t,e)}}function L_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(zt(t,e))return;i.uniform3iv(this.addr,e),Ht(t,e)}}function D_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(zt(t,e))return;i.uniform4iv(this.addr,e),Ht(t,e)}}function I_(i,e){const t=this.cache;t[0]!==e&&(i.uniform1ui(this.addr,e),t[0]=e)}function N_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(zt(t,e))return;i.uniform2uiv(this.addr,e),Ht(t,e)}}function U_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(zt(t,e))return;i.uniform3uiv(this.addr,e),Ht(t,e)}}function O_(i,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(zt(t,e))return;i.uniform4uiv(this.addr,e),Ht(t,e)}}function F_(i,e,t){const n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s);let r;this.type===i.SAMPLER_2D_SHADOW?(pl.compareFunction=t.isReversedDepthBuffer()?kl:Fl,r=pl):r=ad,t.setTexture2D(e||r,s)}function k_(i,e,t){const n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture3D(e||ld,s)}function B_(i,e,t){const n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTextureCube(e||cd,s)}function z_(i,e,t){const n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture2DArray(e||od,s)}function H_(i){switch(i){case 5126:return M_;case 35664:return S_;case 35665:return E_;case 35666:return w_;case 35674:return T_;case 35675:return A_;case 35676:return R_;case 5124:case 35670:return C_;case 35667:case 35671:return P_;case 35668:case 35672:return L_;case 35669:case 35673:return D_;case 5125:return I_;case 36294:return N_;case 36295:return U_;case 36296:return O_;case 35678:case 36198:case 36298:case 36306:case 35682:return F_;case 35679:case 36299:case 36307:return k_;case 35680:case 36300:case 36308:case 36293:return B_;case 36289:case 36303:case 36311:case 36292:return z_}}function V_(i,e){i.uniform1fv(this.addr,e)}function G_(i,e){const t=Ns(e,this.size,2);i.uniform2fv(this.addr,t)}function W_(i,e){const t=Ns(e,this.size,3);i.uniform3fv(this.addr,t)}function $_(i,e){const t=Ns(e,this.size,4);i.uniform4fv(this.addr,t)}function X_(i,e){const t=Ns(e,this.size,4);i.uniformMatrix2fv(this.addr,!1,t)}function q_(i,e){const t=Ns(e,this.size,9);i.uniformMatrix3fv(this.addr,!1,t)}function Y_(i,e){const t=Ns(e,this.size,16);i.uniformMatrix4fv(this.addr,!1,t)}function Z_(i,e){i.uniform1iv(this.addr,e)}function K_(i,e){i.uniform2iv(this.addr,e)}function j_(i,e){i.uniform3iv(this.addr,e)}function J_(i,e){i.uniform4iv(this.addr,e)}function Q_(i,e){i.uniform1uiv(this.addr,e)}function e0(i,e){i.uniform2uiv(this.addr,e)}function t0(i,e){i.uniform3uiv(this.addr,e)}function n0(i,e){i.uniform4uiv(this.addr,e)}function i0(i,e,t){const n=this.cache,s=e.length,r=Ea(t,s);zt(n,r)||(i.uniform1iv(this.addr,r),Ht(n,r));let a;this.type===i.SAMPLER_2D_SHADOW?a=pl:a=ad;for(let o=0;o!==s;++o)t.setTexture2D(e[o]||a,r[o])}function s0(i,e,t){const n=this.cache,s=e.length,r=Ea(t,s);zt(n,r)||(i.uniform1iv(this.addr,r),Ht(n,r));for(let a=0;a!==s;++a)t.setTexture3D(e[a]||ld,r[a])}function r0(i,e,t){const n=this.cache,s=e.length,r=Ea(t,s);zt(n,r)||(i.uniform1iv(this.addr,r),Ht(n,r));for(let a=0;a!==s;++a)t.setTextureCube(e[a]||cd,r[a])}function a0(i,e,t){const n=this.cache,s=e.length,r=Ea(t,s);zt(n,r)||(i.uniform1iv(this.addr,r),Ht(n,r));for(let a=0;a!==s;++a)t.setTexture2DArray(e[a]||od,r[a])}function o0(i){switch(i){case 5126:return V_;case 35664:return G_;case 35665:return W_;case 35666:return $_;case 35674:return X_;case 35675:return q_;case 35676:return Y_;case 5124:case 35670:return Z_;case 35667:case 35671:return K_;case 35668:case 35672:return j_;case 35669:case 35673:return J_;case 5125:return Q_;case 36294:return e0;case 36295:return t0;case 36296:return n0;case 35678:case 36198:case 36298:case 36306:case 35682:return i0;case 35679:case 36299:case 36307:return s0;case 35680:case 36300:case 36308:case 36293:return r0;case 36289:case 36303:case 36311:case 36292:return a0}}class l0{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.setValue=H_(t.type)}}class c0{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=o0(t.type)}}class h0{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,n){const s=this.seq;for(let r=0,a=s.length;r!==a;++r){const o=s[r];o.setValue(e,t[o.id],n)}}}const lo=/(\w+)(\])?(\[|\.)?/g;function fh(i,e){i.seq.push(e),i.map[e.id]=e}function u0(i,e,t){const n=i.name,s=n.length;for(lo.lastIndex=0;;){const r=lo.exec(n),a=lo.lastIndex;let o=r[1];const l=r[2]==="]",c=r[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===s){fh(t,c===void 0?new l0(o,i,e):new c0(o,i,e));break}else{let d=t.map[o];d===void 0&&(d=new h0(o),fh(t,d)),t=d}}}class ia{constructor(e,t){this.seq=[],this.map={};const n=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<n;++a){const o=e.getActiveUniform(t,a),l=e.getUniformLocation(t,o.name);u0(o,l,this)}const s=[],r=[];for(const a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?s.push(a):r.push(a);s.length>0&&(this.seq=s.concat(r))}setValue(e,t,n,s){const r=this.map[t];r!==void 0&&r.setValue(e,n,s)}setOptional(e,t,n){const s=t[n];s!==void 0&&this.setValue(e,n,s)}static upload(e,t,n,s){for(let r=0,a=t.length;r!==a;++r){const o=t[r],l=n[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,s)}}static seqWithValue(e,t){const n=[];for(let s=0,r=e.length;s!==r;++s){const a=e[s];a.id in t&&n.push(a)}return n}}function ph(i,e,t){const n=i.createShader(e);return i.shaderSource(n,t),i.compileShader(n),n}const d0=37297;let f0=0;function p0(i,e){const t=i.split(`
`),n=[],s=Math.max(e-6,0),r=Math.min(e+6,t.length);for(let a=s;a<r;a++){const o=a+1;n.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return n.join(`
`)}const mh=new Xe;function m0(i){et._getMatrix(mh,et.workingColorSpace,i);const e=`mat3( ${mh.elements.map(t=>t.toFixed(4))} )`;switch(et.getTransfer(i)){case la:return[e,"LinearTransferOETF"];case ft:return[e,"sRGBTransferOETF"];default:return ke("WebGLProgram: Unsupported color space: ",i),[e,"LinearTransferOETF"]}}function gh(i,e,t){const n=i.getShaderParameter(e,i.COMPILE_STATUS),r=(i.getShaderInfoLog(e)||"").trim();if(n&&r==="")return"";const a=/ERROR: 0:(\d+)/.exec(r);if(a){const o=parseInt(a[1]);return t.toUpperCase()+`

`+r+`

`+p0(i.getShaderSource(e),o)}else return r}function g0(i,e){const t=m0(e);return[`vec4 ${i}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}const _0={[Cu]:"Linear",[Pu]:"Reinhard",[Lu]:"Cineon",[Du]:"ACESFilmic",[Nu]:"AgX",[Uu]:"Neutral",[Iu]:"Custom"};function v0(i,e){const t=_0[e];return t===void 0?(ke("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+i+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+i+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}const Vr=new P;function x0(){et.getLuminanceCoefficients(Vr);const i=Vr.x.toFixed(4),e=Vr.y.toFixed(4),t=Vr.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function y0(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Ks).join(`
`)}function b0(i){const e=[];for(const t in i){const n=i[t];n!==!1&&e.push("#define "+t+" "+n)}return e.join(`
`)}function M0(i,e){const t={},n=i.getProgramParameter(e,i.ACTIVE_ATTRIBUTES);for(let s=0;s<n;s++){const r=i.getActiveAttrib(e,s),a=r.name;let o=1;r.type===i.FLOAT_MAT2&&(o=2),r.type===i.FLOAT_MAT3&&(o=3),r.type===i.FLOAT_MAT4&&(o=4),t[a]={type:r.type,location:i.getAttribLocation(e,a),locationSize:o}}return t}function Ks(i){return i!==""}function _h(i,e){const t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return i.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function vh(i,e){return i.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const S0=/^[ \t]*#include +<([\w\d./]+)>/gm;function ml(i){return i.replace(S0,w0)}const E0=new Map;function w0(i,e){let t=Ze[e];if(t===void 0){const n=E0.get(e);if(n!==void 0)t=Ze[n],ke('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,n);else throw new Error("THREE.WebGLProgram: Can not resolve #include <"+e+">")}return ml(t)}const T0=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function xh(i){return i.replace(T0,A0)}function A0(i,e,t,n){let s="";for(let r=parseInt(e);r<parseInt(t);r++)s+=n.replace(/\[\s*i\s*\]/g,"[ "+r+" ]").replace(/UNROLLED_LOOP_INDEX/g,r);return s}function yh(i){let e=`precision ${i.precision} float;
	precision ${i.precision} int;
	precision ${i.precision} sampler2D;
	precision ${i.precision} samplerCube;
	precision ${i.precision} sampler3D;
	precision ${i.precision} sampler2DArray;
	precision ${i.precision} sampler2DShadow;
	precision ${i.precision} samplerCubeShadow;
	precision ${i.precision} sampler2DArrayShadow;
	precision ${i.precision} isampler2D;
	precision ${i.precision} isampler3D;
	precision ${i.precision} isamplerCube;
	precision ${i.precision} isampler2DArray;
	precision ${i.precision} usampler2D;
	precision ${i.precision} usampler3D;
	precision ${i.precision} usamplerCube;
	precision ${i.precision} usampler2DArray;
	`;return i.precision==="highp"?e+=`
#define HIGH_PRECISION`:i.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:i.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}const R0={[Jr]:"SHADOWMAP_TYPE_PCF",[Zs]:"SHADOWMAP_TYPE_VSM"};function C0(i){return R0[i.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}const P0={[Fi]:"ENVMAP_TYPE_CUBE",[bs]:"ENVMAP_TYPE_CUBE",[ba]:"ENVMAP_TYPE_CUBE_UV"};function L0(i){return i.envMap===!1?"ENVMAP_TYPE_CUBE":P0[i.envMapMode]||"ENVMAP_TYPE_CUBE"}const D0={[bs]:"ENVMAP_MODE_REFRACTION"};function I0(i){return i.envMap===!1?"ENVMAP_MODE_REFLECTION":D0[i.envMapMode]||"ENVMAP_MODE_REFLECTION"}const N0={[Pl]:"ENVMAP_BLENDING_MULTIPLY",[gf]:"ENVMAP_BLENDING_MIX",[_f]:"ENVMAP_BLENDING_ADD"};function U0(i){return i.envMap===!1?"ENVMAP_BLENDING_NONE":N0[i.combine]||"ENVMAP_BLENDING_NONE"}function O0(i){const e=i.envMapCubeUVHeight;if(e===null)return null;const t=Math.log2(e)-2,n=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:n,maxMip:t}}function F0(i,e,t,n){const s=i.getContext(),r=t.defines;let a=t.vertexShader,o=t.fragmentShader;const l=C0(t),c=L0(t),h=I0(t),d=U0(t),u=O0(t),p=y0(t),g=b0(r),x=s.createProgram();let m,f,M=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(m=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter(Ks).join(`
`),m.length>0&&(m+=`
`),f=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter(Ks).join(`
`),f.length>0&&(f+=`
`)):(m=[yh(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+h:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexNormals?"#define HAS_NORMAL":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Ks).join(`
`),f=[yh(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+h:"",t.envMap?"#define "+d:"",u?"#define CUBEUV_TEXEL_WIDTH "+u.texelWidth:"",u?"#define CUBEUV_TEXEL_HEIGHT "+u.texelHeight:"",u?"#define CUBEUV_MAX_MIP "+u.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor?"#define USE_COLOR":"",t.vertexAlphas||t.batchingColor?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==In?"#define TONE_MAPPING":"",t.toneMapping!==In?Ze.tonemapping_pars_fragment:"",t.toneMapping!==In?v0("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",Ze.colorspace_pars_fragment,g0("linearToOutputTexel",t.outputColorSpace),x0(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(Ks).join(`
`)),a=ml(a),a=_h(a,t),a=vh(a,t),o=ml(o),o=_h(o,t),o=vh(o,t),a=xh(a),o=xh(o),t.isRawShaderMaterial!==!0&&(M=`#version 300 es
`,m=[p,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+m,f=["#define varying in",t.glslVersion===Mc?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===Mc?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+f);const E=M+m+a,y=M+f+o,T=ph(s,s.VERTEX_SHADER,E),S=ph(s,s.FRAGMENT_SHADER,y);s.attachShader(x,T),s.attachShader(x,S),t.index0AttributeName!==void 0?s.bindAttribLocation(x,0,t.index0AttributeName):t.hasPositionAttribute===!0&&s.bindAttribLocation(x,0,"position"),s.linkProgram(x);function R(L){if(i.debug.checkShaderErrors){const N=s.getProgramInfoLog(x)||"",V=s.getShaderInfoLog(T)||"",$=s.getShaderInfoLog(S)||"",F=N.trim(),W=V.trim(),G=$.trim();let J=!0,te=!0;if(s.getProgramParameter(x,s.LINK_STATUS)===!1)if(J=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(s,x,T,S);else{const oe=gh(s,T,"vertex"),me=gh(s,S,"fragment");st("WebGLProgram: Shader Error "+s.getError()+" - VALIDATE_STATUS "+s.getProgramParameter(x,s.VALIDATE_STATUS)+`

Material Name: `+L.name+`
Material Type: `+L.type+`

Program Info Log: `+F+`
`+oe+`
`+me)}else F!==""?ke("WebGLProgram: Program Info Log:",F):(W===""||G==="")&&(te=!1);te&&(L.diagnostics={runnable:J,programLog:F,vertexShader:{log:W,prefix:m},fragmentShader:{log:G,prefix:f}})}s.deleteShader(T),s.deleteShader(S),v=new ia(s,x),w=M0(s,x)}let v;this.getUniforms=function(){return v===void 0&&R(this),v};let w;this.getAttributes=function(){return w===void 0&&R(this),w};let C=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return C===!1&&(C=s.getProgramParameter(x,d0)),C},this.destroy=function(){n.releaseStatesOfProgram(this),s.deleteProgram(x),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=f0++,this.cacheKey=e,this.usedTimes=1,this.program=x,this.vertexShader=T,this.fragmentShader=S,this}let k0=0;class B0{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e,t,n){const s=this._getShaderCacheForMaterial(e);return s.has(t)===!1&&(s.add(t),t.usedTimes++),s.has(n)===!1&&(s.add(n),n.usedTimes++),this}remove(e){const t=this.materialCache.get(e);for(const n of t)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(e),this}getVertexShaderStage(e){return this._getShaderStage(e.vertexShader)}getFragmentShaderStage(e){return this._getShaderStage(e.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const t=this.materialCache;let n=t.get(e);return n===void 0&&(n=new Set,t.set(e,n)),n}_getShaderStage(e){const t=this.shaderCache;let n=t.get(e);return n===void 0&&(n=new z0(e),t.set(e,n)),n}}class z0{constructor(e){this.id=k0++,this.code=e,this.usedTimes=0}}function H0(i){return i===ki||i===ra||i===aa}function V0(i,e,t,n,s,r){const a=new zl,o=new B0,l=new Set,c=[],h=new Map,d=n.logarithmicDepthBuffer;let u=n.precision;const p={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function g(v){return l.add(v),v===0?"uv":`uv${v}`}function x(v,w,C,L,N,V){const $=L.fog,F=N.geometry,W=v.isMeshStandardMaterial||v.isMeshLambertMaterial||v.isMeshPhongMaterial?L.environment:null,G=v.isMeshStandardMaterial||v.isMeshLambertMaterial&&!v.envMap||v.isMeshPhongMaterial&&!v.envMap,J=e.get(v.envMap||W,G),te=J&&J.mapping===ba?J.image.height:null,oe=p[v.type];v.precision!==null&&(u=n.getMaxPrecision(v.precision),u!==v.precision&&ke("WebGLProgram.getParameters:",v.precision,"not supported, using",u,"instead."));const me=F.morphAttributes.position||F.morphAttributes.normal||F.morphAttributes.color,be=me!==void 0?me.length:0;let at=0;F.morphAttributes.position!==void 0&&(at=1),F.morphAttributes.normal!==void 0&&(at=2),F.morphAttributes.color!==void 0&&(at=3);let gt,it,Y,ae;if(oe){const Te=Ln[oe];gt=Te.vertexShader,it=Te.fragmentShader}else{gt=v.vertexShader,it=v.fragmentShader;const Te=o.getVertexShaderStage(v),Ct=o.getFragmentShaderStage(v);o.update(v,Te,Ct),Y=Te.id,ae=Ct.id}const ne=i.getRenderTarget(),Oe=i.state.buffers.depth.getReversed(),Ve=N.isInstancedMesh===!0,Ie=N.isBatchedMesh===!0,Et=!!v.map,Je=!!v.matcap,j=!!J,Ne=!!v.aoMap,ze=!!v.lightMap,ut=!!v.bumpMap&&v.wireframe===!1,xt=!!v.normalMap,It=!!v.displacementMap,$t=!!v.emissiveMap,Rt=!!v.metalnessMap,Nt=!!v.roughnessMap,I=v.anisotropy>0,en=v.clearcoat>0,dt=v.dispersion>0,A=v.iridescence>0,_=v.sheen>0,O=v.transmission>0,z=I&&!!v.anisotropyMap,X=en&&!!v.clearcoatMap,re=en&&!!v.clearcoatNormalMap,ce=en&&!!v.clearcoatRoughnessMap,q=A&&!!v.iridescenceMap,K=A&&!!v.iridescenceThicknessMap,he=_&&!!v.sheenColorMap,Pe=_&&!!v.sheenRoughnessMap,fe=!!v.specularMap,ue=!!v.specularColorMap,Ue=!!v.specularIntensityMap,Be=O&&!!v.transmissionMap,qe=O&&!!v.thicknessMap,D=!!v.gradientMap,le=!!v.alphaMap,Z=v.alphaTest>0,de=!!v.alphaHash,ve=!!v.extensions;let ee=In;v.toneMapped&&(ne===null||ne.isXRRenderTarget===!0)&&(ee=i.toneMapping);const Ce={shaderID:oe,shaderType:v.type,shaderName:v.name,vertexShader:gt,fragmentShader:it,defines:v.defines,customVertexShaderID:Y,customFragmentShaderID:ae,isRawShaderMaterial:v.isRawShaderMaterial===!0,glslVersion:v.glslVersion,precision:u,batching:Ie,batchingColor:Ie&&N._colorsTexture!==null,instancing:Ve,instancingColor:Ve&&N.instanceColor!==null,instancingMorph:Ve&&N.morphTexture!==null,outputColorSpace:ne===null?i.outputColorSpace:ne.isXRRenderTarget===!0?ne.texture.colorSpace:et.workingColorSpace,alphaToCoverage:!!v.alphaToCoverage,map:Et,matcap:Je,envMap:j,envMapMode:j&&J.mapping,envMapCubeUVHeight:te,aoMap:Ne,lightMap:ze,bumpMap:ut,normalMap:xt,displacementMap:It,emissiveMap:$t,normalMapObjectSpace:xt&&v.normalMapType===yf,normalMapTangentSpace:xt&&v.normalMapType===ul,packedNormalMap:xt&&v.normalMapType===ul&&H0(v.normalMap.format),metalnessMap:Rt,roughnessMap:Nt,anisotropy:I,anisotropyMap:z,clearcoat:en,clearcoatMap:X,clearcoatNormalMap:re,clearcoatRoughnessMap:ce,dispersion:dt,iridescence:A,iridescenceMap:q,iridescenceThicknessMap:K,sheen:_,sheenColorMap:he,sheenRoughnessMap:Pe,specularMap:fe,specularColorMap:ue,specularIntensityMap:Ue,transmission:O,transmissionMap:Be,thicknessMap:qe,gradientMap:D,opaque:v.transparent===!1&&v.blending===ms&&v.alphaToCoverage===!1,alphaMap:le,alphaTest:Z,alphaHash:de,combine:v.combine,mapUv:Et&&g(v.map.channel),aoMapUv:Ne&&g(v.aoMap.channel),lightMapUv:ze&&g(v.lightMap.channel),bumpMapUv:ut&&g(v.bumpMap.channel),normalMapUv:xt&&g(v.normalMap.channel),displacementMapUv:It&&g(v.displacementMap.channel),emissiveMapUv:$t&&g(v.emissiveMap.channel),metalnessMapUv:Rt&&g(v.metalnessMap.channel),roughnessMapUv:Nt&&g(v.roughnessMap.channel),anisotropyMapUv:z&&g(v.anisotropyMap.channel),clearcoatMapUv:X&&g(v.clearcoatMap.channel),clearcoatNormalMapUv:re&&g(v.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:ce&&g(v.clearcoatRoughnessMap.channel),iridescenceMapUv:q&&g(v.iridescenceMap.channel),iridescenceThicknessMapUv:K&&g(v.iridescenceThicknessMap.channel),sheenColorMapUv:he&&g(v.sheenColorMap.channel),sheenRoughnessMapUv:Pe&&g(v.sheenRoughnessMap.channel),specularMapUv:fe&&g(v.specularMap.channel),specularColorMapUv:ue&&g(v.specularColorMap.channel),specularIntensityMapUv:Ue&&g(v.specularIntensityMap.channel),transmissionMapUv:Be&&g(v.transmissionMap.channel),thicknessMapUv:qe&&g(v.thicknessMap.channel),alphaMapUv:le&&g(v.alphaMap.channel),vertexTangents:!!F.attributes.tangent&&(xt||I),vertexNormals:!!F.attributes.normal,vertexColors:v.vertexColors,vertexAlphas:v.vertexColors===!0&&!!F.attributes.color&&F.attributes.color.itemSize===4,pointsUvs:N.isPoints===!0&&!!F.attributes.uv&&(Et||le),fog:!!$,useFog:v.fog===!0,fogExp2:!!$&&$.isFogExp2,flatShading:v.wireframe===!1&&(v.flatShading===!0||F.attributes.normal===void 0&&xt===!1&&(v.isMeshLambertMaterial||v.isMeshPhongMaterial||v.isMeshStandardMaterial||v.isMeshPhysicalMaterial)),sizeAttenuation:v.sizeAttenuation===!0,logarithmicDepthBuffer:d,reversedDepthBuffer:Oe,skinning:N.isSkinnedMesh===!0,hasPositionAttribute:F.attributes.position!==void 0,morphTargets:F.morphAttributes.position!==void 0,morphNormals:F.morphAttributes.normal!==void 0,morphColors:F.morphAttributes.color!==void 0,morphTargetsCount:be,morphTextureStride:at,numDirLights:w.directional.length,numPointLights:w.point.length,numSpotLights:w.spot.length,numSpotLightMaps:w.spotLightMap.length,numRectAreaLights:w.rectArea.length,numHemiLights:w.hemi.length,numDirLightShadows:w.directionalShadowMap.length,numPointLightShadows:w.pointShadowMap.length,numSpotLightShadows:w.spotShadowMap.length,numSpotLightShadowsWithMaps:w.numSpotLightShadowsWithMaps,numLightProbes:w.numLightProbes,numLightProbeGrids:V.length,numClippingPlanes:r.numPlanes,numClipIntersection:r.numIntersection,dithering:v.dithering,shadowMapEnabled:i.shadowMap.enabled&&C.length>0,shadowMapType:i.shadowMap.type,toneMapping:ee,decodeVideoTexture:Et&&v.map.isVideoTexture===!0&&et.getTransfer(v.map.colorSpace)===ft,decodeVideoTextureEmissive:$t&&v.emissiveMap.isVideoTexture===!0&&et.getTransfer(v.emissiveMap.colorSpace)===ft,premultipliedAlpha:v.premultipliedAlpha,doubleSided:v.side===pn,flipSided:v.side===rn,useDepthPacking:v.depthPacking>=0,depthPacking:v.depthPacking||0,index0AttributeName:v.index0AttributeName,extensionClipCullDistance:ve&&v.extensions.clipCullDistance===!0&&t.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(ve&&v.extensions.multiDraw===!0||Ie)&&t.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:t.has("KHR_parallel_shader_compile"),customProgramCacheKey:v.customProgramCacheKey()};return Ce.vertexUv1s=l.has(1),Ce.vertexUv2s=l.has(2),Ce.vertexUv3s=l.has(3),l.clear(),Ce}function m(v){const w=[];if(v.shaderID?w.push(v.shaderID):(w.push(v.customVertexShaderID),w.push(v.customFragmentShaderID)),v.defines!==void 0)for(const C in v.defines)w.push(C),w.push(v.defines[C]);return v.isRawShaderMaterial===!1&&(f(w,v),M(w,v),w.push(i.outputColorSpace)),w.push(v.customProgramCacheKey),w.join()}function f(v,w){v.push(w.precision),v.push(w.outputColorSpace),v.push(w.envMapMode),v.push(w.envMapCubeUVHeight),v.push(w.mapUv),v.push(w.alphaMapUv),v.push(w.lightMapUv),v.push(w.aoMapUv),v.push(w.bumpMapUv),v.push(w.normalMapUv),v.push(w.displacementMapUv),v.push(w.emissiveMapUv),v.push(w.metalnessMapUv),v.push(w.roughnessMapUv),v.push(w.anisotropyMapUv),v.push(w.clearcoatMapUv),v.push(w.clearcoatNormalMapUv),v.push(w.clearcoatRoughnessMapUv),v.push(w.iridescenceMapUv),v.push(w.iridescenceThicknessMapUv),v.push(w.sheenColorMapUv),v.push(w.sheenRoughnessMapUv),v.push(w.specularMapUv),v.push(w.specularColorMapUv),v.push(w.specularIntensityMapUv),v.push(w.transmissionMapUv),v.push(w.thicknessMapUv),v.push(w.combine),v.push(w.fogExp2),v.push(w.sizeAttenuation),v.push(w.morphTargetsCount),v.push(w.morphAttributeCount),v.push(w.numDirLights),v.push(w.numPointLights),v.push(w.numSpotLights),v.push(w.numSpotLightMaps),v.push(w.numHemiLights),v.push(w.numRectAreaLights),v.push(w.numDirLightShadows),v.push(w.numPointLightShadows),v.push(w.numSpotLightShadows),v.push(w.numSpotLightShadowsWithMaps),v.push(w.numLightProbes),v.push(w.shadowMapType),v.push(w.toneMapping),v.push(w.numClippingPlanes),v.push(w.numClipIntersection),v.push(w.depthPacking)}function M(v,w){a.disableAll(),w.instancing&&a.enable(0),w.instancingColor&&a.enable(1),w.instancingMorph&&a.enable(2),w.matcap&&a.enable(3),w.envMap&&a.enable(4),w.normalMapObjectSpace&&a.enable(5),w.normalMapTangentSpace&&a.enable(6),w.clearcoat&&a.enable(7),w.iridescence&&a.enable(8),w.alphaTest&&a.enable(9),w.vertexColors&&a.enable(10),w.vertexAlphas&&a.enable(11),w.vertexUv1s&&a.enable(12),w.vertexUv2s&&a.enable(13),w.vertexUv3s&&a.enable(14),w.vertexTangents&&a.enable(15),w.anisotropy&&a.enable(16),w.alphaHash&&a.enable(17),w.batching&&a.enable(18),w.dispersion&&a.enable(19),w.batchingColor&&a.enable(20),w.gradientMap&&a.enable(21),w.packedNormalMap&&a.enable(22),w.vertexNormals&&a.enable(23),v.push(a.mask),a.disableAll(),w.fog&&a.enable(0),w.useFog&&a.enable(1),w.flatShading&&a.enable(2),w.logarithmicDepthBuffer&&a.enable(3),w.reversedDepthBuffer&&a.enable(4),w.skinning&&a.enable(5),w.morphTargets&&a.enable(6),w.morphNormals&&a.enable(7),w.morphColors&&a.enable(8),w.premultipliedAlpha&&a.enable(9),w.shadowMapEnabled&&a.enable(10),w.doubleSided&&a.enable(11),w.flipSided&&a.enable(12),w.useDepthPacking&&a.enable(13),w.dithering&&a.enable(14),w.transmission&&a.enable(15),w.sheen&&a.enable(16),w.opaque&&a.enable(17),w.pointsUvs&&a.enable(18),w.decodeVideoTexture&&a.enable(19),w.decodeVideoTextureEmissive&&a.enable(20),w.alphaToCoverage&&a.enable(21),w.numLightProbeGrids>0&&a.enable(22),w.hasPositionAttribute&&a.enable(23),v.push(a.mask)}function E(v){const w=p[v.type];let C;if(w){const L=Ln[w];C=rp.clone(L.uniforms)}else C=v.uniforms;return C}function y(v,w){let C=h.get(w);return C!==void 0?++C.usedTimes:(C=new F0(i,w,v,s),c.push(C),h.set(w,C)),C}function T(v){if(--v.usedTimes===0){const w=c.indexOf(v);c[w]=c[c.length-1],c.pop(),h.delete(v.cacheKey),v.destroy()}}function S(v){o.remove(v)}function R(){o.dispose()}return{getParameters:x,getProgramCacheKey:m,getUniforms:E,acquireProgram:y,releaseProgram:T,releaseShaderCache:S,programs:c,dispose:R}}function G0(){let i=new WeakMap;function e(a){return i.has(a)}function t(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function s(a,o,l){i.get(a)[o]=l}function r(){i=new WeakMap}return{has:e,get:t,remove:n,update:s,dispose:r}}function W0(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.material.id!==e.material.id?i.material.id-e.material.id:i.materialVariant!==e.materialVariant?i.materialVariant-e.materialVariant:i.z!==e.z?i.z-e.z:i.id-e.id}function bh(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.z!==e.z?e.z-i.z:i.id-e.id}function Mh(){const i=[];let e=0;const t=[],n=[],s=[];function r(){e=0,t.length=0,n.length=0,s.length=0}function a(u){let p=0;return u.isInstancedMesh&&(p+=2),u.isSkinnedMesh&&(p+=1),p}function o(u,p,g,x,m,f){let M=i[e];return M===void 0?(M={id:u.id,object:u,geometry:p,material:g,materialVariant:a(u),groupOrder:x,renderOrder:u.renderOrder,z:m,group:f},i[e]=M):(M.id=u.id,M.object=u,M.geometry=p,M.material=g,M.materialVariant=a(u),M.groupOrder=x,M.renderOrder=u.renderOrder,M.z=m,M.group=f),e++,M}function l(u,p,g,x,m,f){const M=o(u,p,g,x,m,f);g.transmission>0?n.push(M):g.transparent===!0?s.push(M):t.push(M)}function c(u,p,g,x,m,f){const M=o(u,p,g,x,m,f);g.transmission>0?n.unshift(M):g.transparent===!0?s.unshift(M):t.unshift(M)}function h(u,p,g){t.length>1&&t.sort(u||W0),n.length>1&&n.sort(p||bh),s.length>1&&s.sort(p||bh),g&&(t.reverse(),n.reverse(),s.reverse())}function d(){for(let u=e,p=i.length;u<p;u++){const g=i[u];if(g.id===null)break;g.id=null,g.object=null,g.geometry=null,g.material=null,g.group=null}}return{opaque:t,transmissive:n,transparent:s,init:r,push:l,unshift:c,finish:d,sort:h}}function $0(){let i=new WeakMap;function e(n,s){const r=i.get(n);let a;return r===void 0?(a=new Mh,i.set(n,[a])):s>=r.length?(a=new Mh,r.push(a)):a=r[s],a}function t(){i=new WeakMap}return{get:e,dispose:t}}function X0(){const i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new P,color:new ye};break;case"SpotLight":t={position:new P,direction:new P,color:new ye,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new P,color:new ye,distance:0,decay:0};break;case"HemisphereLight":t={direction:new P,skyColor:new ye,groundColor:new ye};break;case"RectAreaLight":t={color:new ye,position:new P,halfWidth:new P,halfHeight:new P};break}return i[e.id]=t,t}}}function q0(){const i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Fe};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Fe};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Fe,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[e.id]=t,t}}}let Y0=0;function Z0(i,e){return(e.castShadow?2:0)-(i.castShadow?2:0)+(e.map?1:0)-(i.map?1:0)}function K0(i){const e=new X0,t=q0(),n={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)n.probe.push(new P);const s=new P,r=new He,a=new He;function o(c){let h=0,d=0,u=0;for(let w=0;w<9;w++)n.probe[w].set(0,0,0);let p=0,g=0,x=0,m=0,f=0,M=0,E=0,y=0,T=0,S=0,R=0;c.sort(Z0);for(let w=0,C=c.length;w<C;w++){const L=c[w],N=L.color,V=L.intensity,$=L.distance;let F=null;if(L.shadow&&L.shadow.map&&(L.shadow.map.texture.format===ki?F=L.shadow.map.texture:F=L.shadow.map.depthTexture||L.shadow.map.texture),L.isAmbientLight)h+=N.r*V,d+=N.g*V,u+=N.b*V;else if(L.isLightProbe){for(let W=0;W<9;W++)n.probe[W].addScaledVector(L.sh.coefficients[W],V);R++}else if(L.isDirectionalLight){const W=e.get(L);if(W.color.copy(L.color).multiplyScalar(L.intensity),L.castShadow){const G=L.shadow,J=t.get(L);J.shadowIntensity=G.intensity,J.shadowBias=G.bias,J.shadowNormalBias=G.normalBias,J.shadowRadius=G.radius,J.shadowMapSize=G.mapSize,n.directionalShadow[p]=J,n.directionalShadowMap[p]=F,n.directionalShadowMatrix[p]=L.shadow.matrix,M++}n.directional[p]=W,p++}else if(L.isSpotLight){const W=e.get(L);W.position.setFromMatrixPosition(L.matrixWorld),W.color.copy(N).multiplyScalar(V),W.distance=$,W.coneCos=Math.cos(L.angle),W.penumbraCos=Math.cos(L.angle*(1-L.penumbra)),W.decay=L.decay,n.spot[x]=W;const G=L.shadow;if(L.map&&(n.spotLightMap[T]=L.map,T++,G.updateMatrices(L),L.castShadow&&S++),n.spotLightMatrix[x]=G.matrix,L.castShadow){const J=t.get(L);J.shadowIntensity=G.intensity,J.shadowBias=G.bias,J.shadowNormalBias=G.normalBias,J.shadowRadius=G.radius,J.shadowMapSize=G.mapSize,n.spotShadow[x]=J,n.spotShadowMap[x]=F,y++}x++}else if(L.isRectAreaLight){const W=e.get(L);W.color.copy(N).multiplyScalar(V),W.halfWidth.set(L.width*.5,0,0),W.halfHeight.set(0,L.height*.5,0),n.rectArea[m]=W,m++}else if(L.isPointLight){const W=e.get(L);if(W.color.copy(L.color).multiplyScalar(L.intensity),W.distance=L.distance,W.decay=L.decay,L.castShadow){const G=L.shadow,J=t.get(L);J.shadowIntensity=G.intensity,J.shadowBias=G.bias,J.shadowNormalBias=G.normalBias,J.shadowRadius=G.radius,J.shadowMapSize=G.mapSize,J.shadowCameraNear=G.camera.near,J.shadowCameraFar=G.camera.far,n.pointShadow[g]=J,n.pointShadowMap[g]=F,n.pointShadowMatrix[g]=L.shadow.matrix,E++}n.point[g]=W,g++}else if(L.isHemisphereLight){const W=e.get(L);W.skyColor.copy(L.color).multiplyScalar(V),W.groundColor.copy(L.groundColor).multiplyScalar(V),n.hemi[f]=W,f++}}m>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=pe.LTC_FLOAT_1,n.rectAreaLTC2=pe.LTC_FLOAT_2):(n.rectAreaLTC1=pe.LTC_HALF_1,n.rectAreaLTC2=pe.LTC_HALF_2)),n.ambient[0]=h,n.ambient[1]=d,n.ambient[2]=u;const v=n.hash;(v.directionalLength!==p||v.pointLength!==g||v.spotLength!==x||v.rectAreaLength!==m||v.hemiLength!==f||v.numDirectionalShadows!==M||v.numPointShadows!==E||v.numSpotShadows!==y||v.numSpotMaps!==T||v.numLightProbes!==R)&&(n.directional.length=p,n.spot.length=x,n.rectArea.length=m,n.point.length=g,n.hemi.length=f,n.directionalShadow.length=M,n.directionalShadowMap.length=M,n.pointShadow.length=E,n.pointShadowMap.length=E,n.spotShadow.length=y,n.spotShadowMap.length=y,n.directionalShadowMatrix.length=M,n.pointShadowMatrix.length=E,n.spotLightMatrix.length=y+T-S,n.spotLightMap.length=T,n.numSpotLightShadowsWithMaps=S,n.numLightProbes=R,v.directionalLength=p,v.pointLength=g,v.spotLength=x,v.rectAreaLength=m,v.hemiLength=f,v.numDirectionalShadows=M,v.numPointShadows=E,v.numSpotShadows=y,v.numSpotMaps=T,v.numLightProbes=R,n.version=Y0++)}function l(c,h){let d=0,u=0,p=0,g=0,x=0;const m=h.matrixWorldInverse;for(let f=0,M=c.length;f<M;f++){const E=c[f];if(E.isDirectionalLight){const y=n.directional[d];y.direction.setFromMatrixPosition(E.matrixWorld),s.setFromMatrixPosition(E.target.matrixWorld),y.direction.sub(s),y.direction.transformDirection(m),d++}else if(E.isSpotLight){const y=n.spot[p];y.position.setFromMatrixPosition(E.matrixWorld),y.position.applyMatrix4(m),y.direction.setFromMatrixPosition(E.matrixWorld),s.setFromMatrixPosition(E.target.matrixWorld),y.direction.sub(s),y.direction.transformDirection(m),p++}else if(E.isRectAreaLight){const y=n.rectArea[g];y.position.setFromMatrixPosition(E.matrixWorld),y.position.applyMatrix4(m),a.identity(),r.copy(E.matrixWorld),r.premultiply(m),a.extractRotation(r),y.halfWidth.set(E.width*.5,0,0),y.halfHeight.set(0,E.height*.5,0),y.halfWidth.applyMatrix4(a),y.halfHeight.applyMatrix4(a),g++}else if(E.isPointLight){const y=n.point[u];y.position.setFromMatrixPosition(E.matrixWorld),y.position.applyMatrix4(m),u++}else if(E.isHemisphereLight){const y=n.hemi[x];y.direction.setFromMatrixPosition(E.matrixWorld),y.direction.transformDirection(m),x++}}}return{setup:o,setupView:l,state:n}}function Sh(i){const e=new K0(i),t=[],n=[],s=[];function r(u){d.camera=u,t.length=0,n.length=0,s.length=0}function a(u){t.push(u)}function o(u){n.push(u)}function l(u){s.push(u)}function c(){e.setup(t)}function h(u){e.setupView(t,u)}const d={lightsArray:t,shadowsArray:n,lightProbeGridArray:s,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:r,state:d,setupLights:c,setupLightsView:h,pushLight:a,pushShadow:o,pushLightProbeGrid:l}}function j0(i){let e=new WeakMap;function t(s,r=0){const a=e.get(s);let o;return a===void 0?(o=new Sh(i),e.set(s,[o])):r>=a.length?(o=new Sh(i),a.push(o)):o=a[r],o}function n(){e=new WeakMap}return{get:t,dispose:n}}const J0=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,Q0=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ).rg;
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ).r;
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( max( 0.0, squared_mean - mean * mean ) );
	gl_FragColor = vec4( mean, std_dev, 0.0, 1.0 );
}`,ev=[new P(1,0,0),new P(-1,0,0),new P(0,1,0),new P(0,-1,0),new P(0,0,1),new P(0,0,-1)],tv=[new P(0,-1,0),new P(0,-1,0),new P(0,0,1),new P(0,0,-1),new P(0,-1,0),new P(0,-1,0)],Eh=new He,$s=new P,co=new P;function nv(i,e,t){let n=new Hl;const s=new Fe,r=new Fe,a=new At,o=new cp,l=new hp,c={},h=t.maxTextureSize,d={[vi]:rn,[rn]:vi,[pn]:pn},u=new En({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Fe},radius:{value:4}},vertexShader:J0,fragmentShader:Q0}),p=u.clone();p.defines.HORIZONTAL_PASS=1;const g=new jt;g.setAttribute("position",new Mn(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const x=new ht(g,u),m=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Jr;let f=this.type;this.render=function(S,R,v){if(m.enabled===!1||m.autoUpdate===!1&&m.needsUpdate===!1||S.length===0)return;this.type===Kd&&(ke("WebGLShadowMap: PCFSoftShadowMap has been deprecated. Using PCFShadowMap instead."),this.type=Jr);const w=i.getRenderTarget(),C=i.getActiveCubeFace(),L=i.getActiveMipmapLevel(),N=i.state;N.setBlending(Yn),N.buffers.depth.getReversed()===!0?N.buffers.color.setClear(0,0,0,0):N.buffers.color.setClear(1,1,1,1),N.buffers.depth.setTest(!0),N.setScissorTest(!1);const V=f!==this.type;V&&R.traverse(function($){$.material&&(Array.isArray($.material)?$.material.forEach(F=>F.needsUpdate=!0):$.material.needsUpdate=!0)});for(let $=0,F=S.length;$<F;$++){const W=S[$],G=W.shadow;if(G===void 0){ke("WebGLShadowMap:",W,"has no shadow.");continue}if(G.autoUpdate===!1&&G.needsUpdate===!1)continue;s.copy(G.mapSize);const J=G.getFrameExtents();s.multiply(J),r.copy(G.mapSize),(s.x>h||s.y>h)&&(s.x>h&&(r.x=Math.floor(h/J.x),s.x=r.x*J.x,G.mapSize.x=r.x),s.y>h&&(r.y=Math.floor(h/J.y),s.y=r.y*J.y,G.mapSize.y=r.y));const te=i.state.buffers.depth.getReversed();if(G.camera._reversedDepth=te,G.map===null||V===!0){if(G.map!==null&&(G.map.depthTexture!==null&&(G.map.depthTexture.dispose(),G.map.depthTexture=null),G.map.dispose()),this.type===Zs){if(W.isPointLight){ke("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}G.map=new Nn(s.x,s.y,{format:ki,type:Kn,minFilter:Zt,magFilter:Zt,generateMipmaps:!1}),G.map.texture.name=W.name+".shadowMap",G.map.depthTexture=new Ms(s.x,s.y,bn),G.map.depthTexture.name=W.name+".shadowMapDepth",G.map.depthTexture.format=jn,G.map.depthTexture.compareFunction=null,G.map.depthTexture.minFilter=Mt,G.map.depthTexture.magFilter=Mt}else W.isPointLight?(G.map=new rd(s.x),G.map.depthTexture=new ip(s.x,On)):(G.map=new Nn(s.x,s.y),G.map.depthTexture=new Ms(s.x,s.y,On)),G.map.depthTexture.name=W.name+".shadowMap",G.map.depthTexture.format=jn,this.type===Jr?(G.map.depthTexture.compareFunction=te?kl:Fl,G.map.depthTexture.minFilter=Zt,G.map.depthTexture.magFilter=Zt):(G.map.depthTexture.compareFunction=null,G.map.depthTexture.minFilter=Mt,G.map.depthTexture.magFilter=Mt);G.camera.updateProjectionMatrix()}const oe=G.map.isWebGLCubeRenderTarget?6:1;for(let me=0;me<oe;me++){if(G.map.isWebGLCubeRenderTarget)i.setRenderTarget(G.map,me),i.clear();else{me===0&&(i.setRenderTarget(G.map),i.clear());const be=G.getViewport(me);a.set(r.x*be.x,r.y*be.y,r.x*be.z,r.y*be.w),N.viewport(a)}if(W.isPointLight){const be=G.camera,at=G.matrix,gt=W.distance||be.far;gt!==be.far&&(be.far=gt,be.updateProjectionMatrix()),$s.setFromMatrixPosition(W.matrixWorld),be.position.copy($s),co.copy(be.position),co.add(ev[me]),be.up.copy(tv[me]),be.lookAt(co),be.updateMatrixWorld(),at.makeTranslation(-$s.x,-$s.y,-$s.z),Eh.multiplyMatrices(be.projectionMatrix,be.matrixWorldInverse),G._frustum.setFromProjectionMatrix(Eh,be.coordinateSystem,be.reversedDepth)}else G.updateMatrices(W);n=G.getFrustum(),y(R,v,G.camera,W,this.type)}G.isPointLightShadow!==!0&&this.type===Zs&&M(G,v),G.needsUpdate=!1}f=this.type,m.needsUpdate=!1,i.setRenderTarget(w,C,L)};function M(S,R){const v=e.update(x);u.defines.VSM_SAMPLES!==S.blurSamples&&(u.defines.VSM_SAMPLES=S.blurSamples,p.defines.VSM_SAMPLES=S.blurSamples,u.needsUpdate=!0,p.needsUpdate=!0),S.mapPass===null&&(S.mapPass=new Nn(s.x,s.y,{format:ki,type:Kn})),u.uniforms.shadow_pass.value=S.map.depthTexture,u.uniforms.resolution.value=S.mapSize,u.uniforms.radius.value=S.radius,i.setRenderTarget(S.mapPass),i.clear(),i.renderBufferDirect(R,null,v,u,x,null),p.uniforms.shadow_pass.value=S.mapPass.texture,p.uniforms.resolution.value=S.mapSize,p.uniforms.radius.value=S.radius,i.setRenderTarget(S.map),i.clear(),i.renderBufferDirect(R,null,v,p,x,null)}function E(S,R,v,w){let C=null;const L=v.isPointLight===!0?S.customDistanceMaterial:S.customDepthMaterial;if(L!==void 0)C=L;else if(C=v.isPointLight===!0?l:o,i.localClippingEnabled&&R.clipShadows===!0&&Array.isArray(R.clippingPlanes)&&R.clippingPlanes.length!==0||R.displacementMap&&R.displacementScale!==0||R.alphaMap&&R.alphaTest>0||R.map&&R.alphaTest>0||R.alphaToCoverage===!0){const N=C.uuid,V=R.uuid;let $=c[N];$===void 0&&($={},c[N]=$);let F=$[V];F===void 0&&(F=C.clone(),$[V]=F,R.addEventListener("dispose",T)),C=F}if(C.visible=R.visible,C.wireframe=R.wireframe,w===Zs?C.side=R.shadowSide!==null?R.shadowSide:R.side:C.side=R.shadowSide!==null?R.shadowSide:d[R.side],C.alphaMap=R.alphaMap,C.alphaTest=R.alphaToCoverage===!0?.5:R.alphaTest,C.map=R.map,C.clipShadows=R.clipShadows,C.clippingPlanes=R.clippingPlanes,C.clipIntersection=R.clipIntersection,C.displacementMap=R.displacementMap,C.displacementScale=R.displacementScale,C.displacementBias=R.displacementBias,C.wireframeLinewidth=R.wireframeLinewidth,C.linewidth=R.linewidth,v.isPointLight===!0&&C.isMeshDistanceMaterial===!0){const N=i.properties.get(C);N.light=v}return C}function y(S,R,v,w,C){if(S.visible===!1)return;if(S.layers.test(R.layers)&&(S.isMesh||S.isLine||S.isPoints)&&(S.castShadow||S.receiveShadow&&C===Zs)&&(!S.frustumCulled||n.intersectsObject(S))){S.modelViewMatrix.multiplyMatrices(v.matrixWorldInverse,S.matrixWorld);const V=e.update(S),$=S.material;if(Array.isArray($)){const F=V.groups;for(let W=0,G=F.length;W<G;W++){const J=F[W],te=$[J.materialIndex];if(te&&te.visible){const oe=E(S,te,w,C);S.onBeforeShadow(i,S,R,v,V,oe,J),i.renderBufferDirect(v,null,V,oe,S,J),S.onAfterShadow(i,S,R,v,V,oe,J)}}}else if($.visible){const F=E(S,$,w,C);S.onBeforeShadow(i,S,R,v,V,F,null),i.renderBufferDirect(v,null,V,F,S,null),S.onAfterShadow(i,S,R,v,V,F,null)}}const N=S.children;for(let V=0,$=N.length;V<$;V++)y(N[V],R,v,w,C)}function T(S){S.target.removeEventListener("dispose",T);for(const v in c){const w=c[v],C=S.target.uuid;C in w&&(w[C].dispose(),delete w[C])}}}function iv(i,e){function t(){let D=!1;const le=new At;let Z=null;const de=new At(0,0,0,0);return{setMask:function(ve){Z!==ve&&!D&&(i.colorMask(ve,ve,ve,ve),Z=ve)},setLocked:function(ve){D=ve},setClear:function(ve,ee,Ce,Te,Ct){Ct===!0&&(ve*=Te,ee*=Te,Ce*=Te),le.set(ve,ee,Ce,Te),de.equals(le)===!1&&(i.clearColor(ve,ee,Ce,Te),de.copy(le))},reset:function(){D=!1,Z=null,de.set(-1,0,0,0)}}}function n(){let D=!1,le=!1,Z=null,de=null,ve=null;return{setReversed:function(ee){if(le!==ee){const Ce=e.get("EXT_clip_control");ee?Ce.clipControlEXT(Ce.LOWER_LEFT_EXT,Ce.ZERO_TO_ONE_EXT):Ce.clipControlEXT(Ce.LOWER_LEFT_EXT,Ce.NEGATIVE_ONE_TO_ONE_EXT),le=ee;const Te=ve;ve=null,this.setClear(Te)}},getReversed:function(){return le},setTest:function(ee){ee?ne(i.DEPTH_TEST):Oe(i.DEPTH_TEST)},setMask:function(ee){Z!==ee&&!D&&(i.depthMask(ee),Z=ee)},setFunc:function(ee){if(le&&(ee=Pf[ee]),de!==ee){switch(ee){case Ao:i.depthFunc(i.NEVER);break;case Ro:i.depthFunc(i.ALWAYS);break;case Co:i.depthFunc(i.LESS);break;case ys:i.depthFunc(i.LEQUAL);break;case Po:i.depthFunc(i.EQUAL);break;case Lo:i.depthFunc(i.GEQUAL);break;case Do:i.depthFunc(i.GREATER);break;case Io:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}de=ee}},setLocked:function(ee){D=ee},setClear:function(ee){ve!==ee&&(ve=ee,le&&(ee=1-ee),i.clearDepth(ee))},reset:function(){D=!1,Z=null,de=null,ve=null,le=!1}}}function s(){let D=!1,le=null,Z=null,de=null,ve=null,ee=null,Ce=null,Te=null,Ct=null;return{setTest:function(yt){D||(yt?ne(i.STENCIL_TEST):Oe(i.STENCIL_TEST))},setMask:function(yt){le!==yt&&!D&&(i.stencilMask(yt),le=yt)},setFunc:function(yt,wn,Tn){(Z!==yt||de!==wn||ve!==Tn)&&(i.stencilFunc(yt,wn,Tn),Z=yt,de=wn,ve=Tn)},setOp:function(yt,wn,Tn){(ee!==yt||Ce!==wn||Te!==Tn)&&(i.stencilOp(yt,wn,Tn),ee=yt,Ce=wn,Te=Tn)},setLocked:function(yt){D=yt},setClear:function(yt){Ct!==yt&&(i.clearStencil(yt),Ct=yt)},reset:function(){D=!1,le=null,Z=null,de=null,ve=null,ee=null,Ce=null,Te=null,Ct=null}}}const r=new t,a=new n,o=new s,l=new WeakMap,c=new WeakMap;let h={},d={},u={},p=new WeakMap,g=[],x=null,m=!1,f=null,M=null,E=null,y=null,T=null,S=null,R=null,v=new ye(0,0,0),w=0,C=!1,L=null,N=null,V=null,$=null,F=null;const W=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let G=!1,J=0;const te=i.getParameter(i.VERSION);te.indexOf("WebGL")!==-1?(J=parseFloat(/^WebGL (\d)/.exec(te)[1]),G=J>=1):te.indexOf("OpenGL ES")!==-1&&(J=parseFloat(/^OpenGL ES (\d)/.exec(te)[1]),G=J>=2);let oe=null,me={};const be=i.getParameter(i.SCISSOR_BOX),at=i.getParameter(i.VIEWPORT),gt=new At().fromArray(be),it=new At().fromArray(at);function Y(D,le,Z,de){const ve=new Uint8Array(4),ee=i.createTexture();i.bindTexture(D,ee),i.texParameteri(D,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(D,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let Ce=0;Ce<Z;Ce++)D===i.TEXTURE_3D||D===i.TEXTURE_2D_ARRAY?i.texImage3D(le,0,i.RGBA,1,1,de,0,i.RGBA,i.UNSIGNED_BYTE,ve):i.texImage2D(le+Ce,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,ve);return ee}const ae={};ae[i.TEXTURE_2D]=Y(i.TEXTURE_2D,i.TEXTURE_2D,1),ae[i.TEXTURE_CUBE_MAP]=Y(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),ae[i.TEXTURE_2D_ARRAY]=Y(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),ae[i.TEXTURE_3D]=Y(i.TEXTURE_3D,i.TEXTURE_3D,1,1),r.setClear(0,0,0,1),a.setClear(1),o.setClear(0),ne(i.DEPTH_TEST),a.setFunc(ys),ut(!1),xt(gc),ne(i.CULL_FACE),Ne(Yn);function ne(D){h[D]!==!0&&(i.enable(D),h[D]=!0)}function Oe(D){h[D]!==!1&&(i.disable(D),h[D]=!1)}function Ve(D,le){return u[D]!==le?(i.bindFramebuffer(D,le),u[D]=le,D===i.DRAW_FRAMEBUFFER&&(u[i.FRAMEBUFFER]=le),D===i.FRAMEBUFFER&&(u[i.DRAW_FRAMEBUFFER]=le),!0):!1}function Ie(D,le){let Z=g,de=!1;if(D){Z=p.get(le),Z===void 0&&(Z=[],p.set(le,Z));const ve=D.textures;if(Z.length!==ve.length||Z[0]!==i.COLOR_ATTACHMENT0){for(let ee=0,Ce=ve.length;ee<Ce;ee++)Z[ee]=i.COLOR_ATTACHMENT0+ee;Z.length=ve.length,de=!0}}else Z[0]!==i.BACK&&(Z[0]=i.BACK,de=!0);de&&i.drawBuffers(Z)}function Et(D){return x!==D?(i.useProgram(D),x=D,!0):!1}const Je={[Ii]:i.FUNC_ADD,[Jd]:i.FUNC_SUBTRACT,[Qd]:i.FUNC_REVERSE_SUBTRACT};Je[ef]=i.MIN,Je[tf]=i.MAX;const j={[nf]:i.ZERO,[sf]:i.ONE,[rf]:i.SRC_COLOR,[wo]:i.SRC_ALPHA,[uf]:i.SRC_ALPHA_SATURATE,[cf]:i.DST_COLOR,[of]:i.DST_ALPHA,[af]:i.ONE_MINUS_SRC_COLOR,[To]:i.ONE_MINUS_SRC_ALPHA,[hf]:i.ONE_MINUS_DST_COLOR,[lf]:i.ONE_MINUS_DST_ALPHA,[df]:i.CONSTANT_COLOR,[ff]:i.ONE_MINUS_CONSTANT_COLOR,[pf]:i.CONSTANT_ALPHA,[mf]:i.ONE_MINUS_CONSTANT_ALPHA};function Ne(D,le,Z,de,ve,ee,Ce,Te,Ct,yt){if(D===Yn){m===!0&&(Oe(i.BLEND),m=!1);return}if(m===!1&&(ne(i.BLEND),m=!0),D!==jd){if(D!==f||yt!==C){if((M!==Ii||T!==Ii)&&(i.blendEquation(i.FUNC_ADD),M=Ii,T=Ii),yt)switch(D){case ms:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case _c:i.blendFunc(i.ONE,i.ONE);break;case vc:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case xc:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:st("WebGLState: Invalid blending: ",D);break}else switch(D){case ms:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case _c:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case vc:st("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case xc:st("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:st("WebGLState: Invalid blending: ",D);break}E=null,y=null,S=null,R=null,v.set(0,0,0),w=0,f=D,C=yt}return}ve=ve||le,ee=ee||Z,Ce=Ce||de,(le!==M||ve!==T)&&(i.blendEquationSeparate(Je[le],Je[ve]),M=le,T=ve),(Z!==E||de!==y||ee!==S||Ce!==R)&&(i.blendFuncSeparate(j[Z],j[de],j[ee],j[Ce]),E=Z,y=de,S=ee,R=Ce),(Te.equals(v)===!1||Ct!==w)&&(i.blendColor(Te.r,Te.g,Te.b,Ct),v.copy(Te),w=Ct),f=D,C=!1}function ze(D,le){D.side===pn?Oe(i.CULL_FACE):ne(i.CULL_FACE);let Z=D.side===rn;le&&(Z=!Z),ut(Z),D.blending===ms&&D.transparent===!1?Ne(Yn):Ne(D.blending,D.blendEquation,D.blendSrc,D.blendDst,D.blendEquationAlpha,D.blendSrcAlpha,D.blendDstAlpha,D.blendColor,D.blendAlpha,D.premultipliedAlpha),a.setFunc(D.depthFunc),a.setTest(D.depthTest),a.setMask(D.depthWrite),r.setMask(D.colorWrite);const de=D.stencilWrite;o.setTest(de),de&&(o.setMask(D.stencilWriteMask),o.setFunc(D.stencilFunc,D.stencilRef,D.stencilFuncMask),o.setOp(D.stencilFail,D.stencilZFail,D.stencilZPass)),$t(D.polygonOffset,D.polygonOffsetFactor,D.polygonOffsetUnits),D.alphaToCoverage===!0?ne(i.SAMPLE_ALPHA_TO_COVERAGE):Oe(i.SAMPLE_ALPHA_TO_COVERAGE)}function ut(D){L!==D&&(D?i.frontFace(i.CW):i.frontFace(i.CCW),L=D)}function xt(D){D!==Yd?(ne(i.CULL_FACE),D!==N&&(D===gc?i.cullFace(i.BACK):D===Zd?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):Oe(i.CULL_FACE),N=D}function It(D){D!==V&&(G&&i.lineWidth(D),V=D)}function $t(D,le,Z){D?(ne(i.POLYGON_OFFSET_FILL),($!==le||F!==Z)&&($=le,F=Z,a.getReversed()&&(le=-le),i.polygonOffset(le,Z))):Oe(i.POLYGON_OFFSET_FILL)}function Rt(D){D?ne(i.SCISSOR_TEST):Oe(i.SCISSOR_TEST)}function Nt(D){D===void 0&&(D=i.TEXTURE0+W-1),oe!==D&&(i.activeTexture(D),oe=D)}function I(D,le,Z){Z===void 0&&(oe===null?Z=i.TEXTURE0+W-1:Z=oe);let de=me[Z];de===void 0&&(de={type:void 0,texture:void 0},me[Z]=de),(de.type!==D||de.texture!==le)&&(oe!==Z&&(i.activeTexture(Z),oe=Z),i.bindTexture(D,le||ae[D]),de.type=D,de.texture=le)}function en(){const D=me[oe];D!==void 0&&D.type!==void 0&&(i.bindTexture(D.type,null),D.type=void 0,D.texture=void 0)}function dt(){try{i.compressedTexImage2D(...arguments)}catch(D){st("WebGLState:",D)}}function A(){try{i.compressedTexImage3D(...arguments)}catch(D){st("WebGLState:",D)}}function _(){try{i.texSubImage2D(...arguments)}catch(D){st("WebGLState:",D)}}function O(){try{i.texSubImage3D(...arguments)}catch(D){st("WebGLState:",D)}}function z(){try{i.compressedTexSubImage2D(...arguments)}catch(D){st("WebGLState:",D)}}function X(){try{i.compressedTexSubImage3D(...arguments)}catch(D){st("WebGLState:",D)}}function re(){try{i.texStorage2D(...arguments)}catch(D){st("WebGLState:",D)}}function ce(){try{i.texStorage3D(...arguments)}catch(D){st("WebGLState:",D)}}function q(){try{i.texImage2D(...arguments)}catch(D){st("WebGLState:",D)}}function K(){try{i.texImage3D(...arguments)}catch(D){st("WebGLState:",D)}}function he(D){return d[D]!==void 0?d[D]:i.getParameter(D)}function Pe(D,le){d[D]!==le&&(i.pixelStorei(D,le),d[D]=le)}function fe(D){gt.equals(D)===!1&&(i.scissor(D.x,D.y,D.z,D.w),gt.copy(D))}function ue(D){it.equals(D)===!1&&(i.viewport(D.x,D.y,D.z,D.w),it.copy(D))}function Ue(D,le){let Z=c.get(le);Z===void 0&&(Z=new WeakMap,c.set(le,Z));let de=Z.get(D);de===void 0&&(de=i.getUniformBlockIndex(le,D.name),Z.set(D,de))}function Be(D,le){const de=c.get(le).get(D);l.get(le)!==de&&(i.uniformBlockBinding(le,de,D.__bindingPointIndex),l.set(le,de))}function qe(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),i.pixelStorei(i.PACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,!1),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,i.BROWSER_DEFAULT_WEBGL),i.pixelStorei(i.PACK_ROW_LENGTH,0),i.pixelStorei(i.PACK_SKIP_PIXELS,0),i.pixelStorei(i.PACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_ROW_LENGTH,0),i.pixelStorei(i.UNPACK_IMAGE_HEIGHT,0),i.pixelStorei(i.UNPACK_SKIP_PIXELS,0),i.pixelStorei(i.UNPACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_SKIP_IMAGES,0),h={},d={},oe=null,me={},u={},p=new WeakMap,g=[],x=null,m=!1,f=null,M=null,E=null,y=null,T=null,S=null,R=null,v=new ye(0,0,0),w=0,C=!1,L=null,N=null,V=null,$=null,F=null,gt.set(0,0,i.canvas.width,i.canvas.height),it.set(0,0,i.canvas.width,i.canvas.height),r.reset(),a.reset(),o.reset()}return{buffers:{color:r,depth:a,stencil:o},enable:ne,disable:Oe,bindFramebuffer:Ve,drawBuffers:Ie,useProgram:Et,setBlending:Ne,setMaterial:ze,setFlipSided:ut,setCullFace:xt,setLineWidth:It,setPolygonOffset:$t,setScissorTest:Rt,activeTexture:Nt,bindTexture:I,unbindTexture:en,compressedTexImage2D:dt,compressedTexImage3D:A,texImage2D:q,texImage3D:K,pixelStorei:Pe,getParameter:he,updateUBOMapping:Ue,uniformBlockBinding:Be,texStorage2D:re,texStorage3D:ce,texSubImage2D:_,texSubImage3D:O,compressedTexSubImage2D:z,compressedTexSubImage3D:X,scissor:fe,viewport:ue,reset:qe}}function sv(i,e,t,n,s,r,a){const o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new Fe,h=new WeakMap,d=new Set;let u;const p=new WeakMap;let g=!1;try{g=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function x(A,_){return g?new OffscreenCanvas(A,_):ca("canvas")}function m(A,_,O){let z=1;const X=dt(A);if((X.width>O||X.height>O)&&(z=O/Math.max(X.width,X.height)),z<1)if(typeof HTMLImageElement<"u"&&A instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&A instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&A instanceof ImageBitmap||typeof VideoFrame<"u"&&A instanceof VideoFrame){const re=Math.floor(z*X.width),ce=Math.floor(z*X.height);u===void 0&&(u=x(re,ce));const q=_?x(re,ce):u;return q.width=re,q.height=ce,q.getContext("2d").drawImage(A,0,0,re,ce),ke("WebGLRenderer: Texture has been resized from ("+X.width+"x"+X.height+") to ("+re+"x"+ce+")."),q}else return"data"in A&&ke("WebGLRenderer: Image in DataTexture is too big ("+X.width+"x"+X.height+")."),A;return A}function f(A){return A.generateMipmaps}function M(A){i.generateMipmap(A)}function E(A){return A.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:A.isWebGL3DRenderTarget?i.TEXTURE_3D:A.isWebGLArrayRenderTarget||A.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function y(A,_,O,z,X,re=!1){if(A!==null){if(i[A]!==void 0)return i[A];ke("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+A+"'")}let ce;z&&(ce=e.get("EXT_texture_norm16"),ce||ke("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let q=_;if(_===i.RED&&(O===i.FLOAT&&(q=i.R32F),O===i.HALF_FLOAT&&(q=i.R16F),O===i.UNSIGNED_BYTE&&(q=i.R8),O===i.UNSIGNED_SHORT&&ce&&(q=ce.R16_EXT),O===i.SHORT&&ce&&(q=ce.R16_SNORM_EXT)),_===i.RED_INTEGER&&(O===i.UNSIGNED_BYTE&&(q=i.R8UI),O===i.UNSIGNED_SHORT&&(q=i.R16UI),O===i.UNSIGNED_INT&&(q=i.R32UI),O===i.BYTE&&(q=i.R8I),O===i.SHORT&&(q=i.R16I),O===i.INT&&(q=i.R32I)),_===i.RG&&(O===i.FLOAT&&(q=i.RG32F),O===i.HALF_FLOAT&&(q=i.RG16F),O===i.UNSIGNED_BYTE&&(q=i.RG8),O===i.UNSIGNED_SHORT&&ce&&(q=ce.RG16_EXT),O===i.SHORT&&ce&&(q=ce.RG16_SNORM_EXT)),_===i.RG_INTEGER&&(O===i.UNSIGNED_BYTE&&(q=i.RG8UI),O===i.UNSIGNED_SHORT&&(q=i.RG16UI),O===i.UNSIGNED_INT&&(q=i.RG32UI),O===i.BYTE&&(q=i.RG8I),O===i.SHORT&&(q=i.RG16I),O===i.INT&&(q=i.RG32I)),_===i.RGB_INTEGER&&(O===i.UNSIGNED_BYTE&&(q=i.RGB8UI),O===i.UNSIGNED_SHORT&&(q=i.RGB16UI),O===i.UNSIGNED_INT&&(q=i.RGB32UI),O===i.BYTE&&(q=i.RGB8I),O===i.SHORT&&(q=i.RGB16I),O===i.INT&&(q=i.RGB32I)),_===i.RGBA_INTEGER&&(O===i.UNSIGNED_BYTE&&(q=i.RGBA8UI),O===i.UNSIGNED_SHORT&&(q=i.RGBA16UI),O===i.UNSIGNED_INT&&(q=i.RGBA32UI),O===i.BYTE&&(q=i.RGBA8I),O===i.SHORT&&(q=i.RGBA16I),O===i.INT&&(q=i.RGBA32I)),_===i.RGB&&(O===i.UNSIGNED_SHORT&&ce&&(q=ce.RGB16_EXT),O===i.SHORT&&ce&&(q=ce.RGB16_SNORM_EXT),O===i.UNSIGNED_INT_5_9_9_9_REV&&(q=i.RGB9_E5),O===i.UNSIGNED_INT_10F_11F_11F_REV&&(q=i.R11F_G11F_B10F)),_===i.RGBA){const K=re?la:et.getTransfer(X);O===i.FLOAT&&(q=i.RGBA32F),O===i.HALF_FLOAT&&(q=i.RGBA16F),O===i.UNSIGNED_BYTE&&(q=K===ft?i.SRGB8_ALPHA8:i.RGBA8),O===i.UNSIGNED_SHORT&&ce&&(q=ce.RGBA16_EXT),O===i.SHORT&&ce&&(q=ce.RGBA16_SNORM_EXT),O===i.UNSIGNED_SHORT_4_4_4_4&&(q=i.RGBA4),O===i.UNSIGNED_SHORT_5_5_5_1&&(q=i.RGB5_A1)}return(q===i.R16F||q===i.R32F||q===i.RG16F||q===i.RG32F||q===i.RGBA16F||q===i.RGBA32F)&&e.get("EXT_color_buffer_float"),q}function T(A,_){let O;return A?_===null||_===On||_===ir?O=i.DEPTH24_STENCIL8:_===bn?O=i.DEPTH32F_STENCIL8:_===nr&&(O=i.DEPTH24_STENCIL8,ke("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):_===null||_===On||_===ir?O=i.DEPTH_COMPONENT24:_===bn?O=i.DEPTH_COMPONENT32F:_===nr&&(O=i.DEPTH_COMPONENT16),O}function S(A,_){return f(A)===!0||A.isFramebufferTexture&&A.minFilter!==Mt&&A.minFilter!==Zt?Math.log2(Math.max(_.width,_.height))+1:A.mipmaps!==void 0&&A.mipmaps.length>0?A.mipmaps.length:A.isCompressedTexture&&Array.isArray(A.image)?_.mipmaps.length:1}function R(A){const _=A.target;_.removeEventListener("dispose",R),w(_),_.isVideoTexture&&h.delete(_),_.isHTMLTexture&&d.delete(_)}function v(A){const _=A.target;_.removeEventListener("dispose",v),L(_)}function w(A){const _=n.get(A);if(_.__webglInit===void 0)return;const O=A.source,z=p.get(O);if(z){const X=z[_.__cacheKey];X.usedTimes--,X.usedTimes===0&&C(A),Object.keys(z).length===0&&p.delete(O)}n.remove(A)}function C(A){const _=n.get(A);i.deleteTexture(_.__webglTexture);const O=A.source,z=p.get(O);delete z[_.__cacheKey],a.memory.textures--}function L(A){const _=n.get(A);if(A.depthTexture&&(A.depthTexture.dispose(),n.remove(A.depthTexture)),A.isWebGLCubeRenderTarget)for(let z=0;z<6;z++){if(Array.isArray(_.__webglFramebuffer[z]))for(let X=0;X<_.__webglFramebuffer[z].length;X++)i.deleteFramebuffer(_.__webglFramebuffer[z][X]);else i.deleteFramebuffer(_.__webglFramebuffer[z]);_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer[z])}else{if(Array.isArray(_.__webglFramebuffer))for(let z=0;z<_.__webglFramebuffer.length;z++)i.deleteFramebuffer(_.__webglFramebuffer[z]);else i.deleteFramebuffer(_.__webglFramebuffer);if(_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer),_.__webglMultisampledFramebuffer&&i.deleteFramebuffer(_.__webglMultisampledFramebuffer),_.__webglColorRenderbuffer)for(let z=0;z<_.__webglColorRenderbuffer.length;z++)_.__webglColorRenderbuffer[z]&&i.deleteRenderbuffer(_.__webglColorRenderbuffer[z]);_.__webglDepthRenderbuffer&&i.deleteRenderbuffer(_.__webglDepthRenderbuffer)}const O=A.textures;for(let z=0,X=O.length;z<X;z++){const re=n.get(O[z]);re.__webglTexture&&(i.deleteTexture(re.__webglTexture),a.memory.textures--),n.remove(O[z])}n.remove(A)}let N=0;function V(){N=0}function $(){return N}function F(A){N=A}function W(){const A=N;return A>=s.maxTextures&&ke("WebGLTextures: Trying to use "+A+" texture units while this GPU supports only "+s.maxTextures),N+=1,A}function G(A){const _=[];return _.push(A.wrapS),_.push(A.wrapT),_.push(A.wrapR||0),_.push(A.magFilter),_.push(A.minFilter),_.push(A.anisotropy),_.push(A.internalFormat),_.push(A.format),_.push(A.type),_.push(A.generateMipmaps),_.push(A.premultiplyAlpha),_.push(A.flipY),_.push(A.unpackAlignment),_.push(A.colorSpace),_.join()}function J(A,_){const O=n.get(A);if(A.isVideoTexture&&I(A),A.isRenderTargetTexture===!1&&A.isExternalTexture!==!0&&A.version>0&&O.__version!==A.version){const z=A.image;if(z===null)ke("WebGLRenderer: Texture marked for update but no image data found.");else if(z.complete===!1)ke("WebGLRenderer: Texture marked for update but image is incomplete");else{Oe(O,A,_);return}}else A.isExternalTexture&&(O.__webglTexture=A.sourceTexture?A.sourceTexture:null);t.bindTexture(i.TEXTURE_2D,O.__webglTexture,i.TEXTURE0+_)}function te(A,_){const O=n.get(A);if(A.isRenderTargetTexture===!1&&A.version>0&&O.__version!==A.version){Oe(O,A,_);return}else A.isExternalTexture&&(O.__webglTexture=A.sourceTexture?A.sourceTexture:null);t.bindTexture(i.TEXTURE_2D_ARRAY,O.__webglTexture,i.TEXTURE0+_)}function oe(A,_){const O=n.get(A);if(A.isRenderTargetTexture===!1&&A.version>0&&O.__version!==A.version){Oe(O,A,_);return}t.bindTexture(i.TEXTURE_3D,O.__webglTexture,i.TEXTURE0+_)}function me(A,_){const O=n.get(A);if(A.isCubeDepthTexture!==!0&&A.version>0&&O.__version!==A.version){Ve(O,A,_);return}t.bindTexture(i.TEXTURE_CUBE_MAP,O.__webglTexture,i.TEXTURE0+_)}const be={[tr]:i.REPEAT,[Wn]:i.CLAMP_TO_EDGE,[No]:i.MIRRORED_REPEAT},at={[Mt]:i.NEAREST,[vf]:i.NEAREST_MIPMAP_NEAREST,[mr]:i.NEAREST_MIPMAP_LINEAR,[Zt]:i.LINEAR,[La]:i.LINEAR_MIPMAP_NEAREST,[$n]:i.LINEAR_MIPMAP_LINEAR},gt={[bf]:i.NEVER,[Tf]:i.ALWAYS,[Mf]:i.LESS,[Fl]:i.LEQUAL,[Sf]:i.EQUAL,[kl]:i.GEQUAL,[Ef]:i.GREATER,[wf]:i.NOTEQUAL};function it(A,_){if(_.type===bn&&e.has("OES_texture_float_linear")===!1&&(_.magFilter===Zt||_.magFilter===La||_.magFilter===mr||_.magFilter===$n||_.minFilter===Zt||_.minFilter===La||_.minFilter===mr||_.minFilter===$n)&&ke("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(A,i.TEXTURE_WRAP_S,be[_.wrapS]),i.texParameteri(A,i.TEXTURE_WRAP_T,be[_.wrapT]),(A===i.TEXTURE_3D||A===i.TEXTURE_2D_ARRAY)&&i.texParameteri(A,i.TEXTURE_WRAP_R,be[_.wrapR]),i.texParameteri(A,i.TEXTURE_MAG_FILTER,at[_.magFilter]),i.texParameteri(A,i.TEXTURE_MIN_FILTER,at[_.minFilter]),_.compareFunction&&(i.texParameteri(A,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(A,i.TEXTURE_COMPARE_FUNC,gt[_.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(_.magFilter===Mt||_.minFilter!==mr&&_.minFilter!==$n||_.type===bn&&e.has("OES_texture_float_linear")===!1)return;if(_.anisotropy>1||n.get(_).__currentAnisotropy){const O=e.get("EXT_texture_filter_anisotropic");i.texParameterf(A,O.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(_.anisotropy,s.getMaxAnisotropy())),n.get(_).__currentAnisotropy=_.anisotropy}}}function Y(A,_){let O=!1;A.__webglInit===void 0&&(A.__webglInit=!0,_.addEventListener("dispose",R));const z=_.source;let X=p.get(z);X===void 0&&(X={},p.set(z,X));const re=G(_);if(re!==A.__cacheKey){X[re]===void 0&&(X[re]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,O=!0),X[re].usedTimes++;const ce=X[A.__cacheKey];ce!==void 0&&(X[A.__cacheKey].usedTimes--,ce.usedTimes===0&&C(_)),A.__cacheKey=re,A.__webglTexture=X[re].texture}return O}function ae(A,_,O){return Math.floor(Math.floor(A/O)/_)}function ne(A,_,O,z){const re=A.updateRanges;if(re.length===0)t.texSubImage2D(i.TEXTURE_2D,0,0,0,_.width,_.height,O,z,_.data);else{re.sort((Pe,fe)=>Pe.start-fe.start);let ce=0;for(let Pe=1;Pe<re.length;Pe++){const fe=re[ce],ue=re[Pe],Ue=fe.start+fe.count,Be=ae(ue.start,_.width,4),qe=ae(fe.start,_.width,4);ue.start<=Ue+1&&Be===qe&&ae(ue.start+ue.count-1,_.width,4)===Be?fe.count=Math.max(fe.count,ue.start+ue.count-fe.start):(++ce,re[ce]=ue)}re.length=ce+1;const q=t.getParameter(i.UNPACK_ROW_LENGTH),K=t.getParameter(i.UNPACK_SKIP_PIXELS),he=t.getParameter(i.UNPACK_SKIP_ROWS);t.pixelStorei(i.UNPACK_ROW_LENGTH,_.width);for(let Pe=0,fe=re.length;Pe<fe;Pe++){const ue=re[Pe],Ue=Math.floor(ue.start/4),Be=Math.ceil(ue.count/4),qe=Ue%_.width,D=Math.floor(Ue/_.width),le=Be,Z=1;t.pixelStorei(i.UNPACK_SKIP_PIXELS,qe),t.pixelStorei(i.UNPACK_SKIP_ROWS,D),t.texSubImage2D(i.TEXTURE_2D,0,qe,D,le,Z,O,z,_.data)}A.clearUpdateRanges(),t.pixelStorei(i.UNPACK_ROW_LENGTH,q),t.pixelStorei(i.UNPACK_SKIP_PIXELS,K),t.pixelStorei(i.UNPACK_SKIP_ROWS,he)}}function Oe(A,_,O){let z=i.TEXTURE_2D;(_.isDataArrayTexture||_.isCompressedArrayTexture)&&(z=i.TEXTURE_2D_ARRAY),_.isData3DTexture&&(z=i.TEXTURE_3D);const X=Y(A,_),re=_.source;t.bindTexture(z,A.__webglTexture,i.TEXTURE0+O);const ce=n.get(re);if(re.version!==ce.__version||X===!0){if(t.activeTexture(i.TEXTURE0+O),(typeof ImageBitmap<"u"&&_.image instanceof ImageBitmap)===!1){const Z=et.getPrimaries(et.workingColorSpace),de=_.colorSpace===Gn?null:et.getPrimaries(_.colorSpace),ve=_.colorSpace===Gn||Z===de?i.NONE:i.BROWSER_DEFAULT_WEBGL;t.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),t.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),t.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,ve)}t.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment);let K=m(_.image,!1,s.maxTextureSize);K=en(_,K);const he=r.convert(_.format,_.colorSpace),Pe=r.convert(_.type);let fe=y(_.internalFormat,he,Pe,_.normalized,_.colorSpace,_.isVideoTexture);it(z,_);let ue;const Ue=_.mipmaps,Be=_.isVideoTexture!==!0,qe=ce.__version===void 0||X===!0,D=re.dataReady,le=S(_,K);if(_.isDepthTexture)fe=T(_.format===Ui,_.type),qe&&(Be?t.texStorage2D(i.TEXTURE_2D,1,fe,K.width,K.height):t.texImage2D(i.TEXTURE_2D,0,fe,K.width,K.height,0,he,Pe,null));else if(_.isDataTexture)if(Ue.length>0){Be&&qe&&t.texStorage2D(i.TEXTURE_2D,le,fe,Ue[0].width,Ue[0].height);for(let Z=0,de=Ue.length;Z<de;Z++)ue=Ue[Z],Be?D&&t.texSubImage2D(i.TEXTURE_2D,Z,0,0,ue.width,ue.height,he,Pe,ue.data):t.texImage2D(i.TEXTURE_2D,Z,fe,ue.width,ue.height,0,he,Pe,ue.data);_.generateMipmaps=!1}else Be?(qe&&t.texStorage2D(i.TEXTURE_2D,le,fe,K.width,K.height),D&&ne(_,K,he,Pe)):t.texImage2D(i.TEXTURE_2D,0,fe,K.width,K.height,0,he,Pe,K.data);else if(_.isCompressedTexture)if(_.isCompressedArrayTexture){Be&&qe&&t.texStorage3D(i.TEXTURE_2D_ARRAY,le,fe,Ue[0].width,Ue[0].height,K.depth);for(let Z=0,de=Ue.length;Z<de;Z++)if(ue=Ue[Z],_.format!==gn)if(he!==null)if(Be){if(D)if(_.layerUpdates.size>0){const ve=th(ue.width,ue.height,_.format,_.type);for(const ee of _.layerUpdates){const Ce=ue.data.subarray(ee*ve/ue.data.BYTES_PER_ELEMENT,(ee+1)*ve/ue.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,Z,0,0,ee,ue.width,ue.height,1,he,Ce)}_.clearLayerUpdates()}else t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,Z,0,0,0,ue.width,ue.height,K.depth,he,ue.data)}else t.compressedTexImage3D(i.TEXTURE_2D_ARRAY,Z,fe,ue.width,ue.height,K.depth,0,ue.data,0,0);else ke("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else Be?D&&t.texSubImage3D(i.TEXTURE_2D_ARRAY,Z,0,0,0,ue.width,ue.height,K.depth,he,Pe,ue.data):t.texImage3D(i.TEXTURE_2D_ARRAY,Z,fe,ue.width,ue.height,K.depth,0,he,Pe,ue.data)}else{Be&&qe&&t.texStorage2D(i.TEXTURE_2D,le,fe,Ue[0].width,Ue[0].height);for(let Z=0,de=Ue.length;Z<de;Z++)ue=Ue[Z],_.format!==gn?he!==null?Be?D&&t.compressedTexSubImage2D(i.TEXTURE_2D,Z,0,0,ue.width,ue.height,he,ue.data):t.compressedTexImage2D(i.TEXTURE_2D,Z,fe,ue.width,ue.height,0,ue.data):ke("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):Be?D&&t.texSubImage2D(i.TEXTURE_2D,Z,0,0,ue.width,ue.height,he,Pe,ue.data):t.texImage2D(i.TEXTURE_2D,Z,fe,ue.width,ue.height,0,he,Pe,ue.data)}else if(_.isDataArrayTexture)if(Be){if(qe&&t.texStorage3D(i.TEXTURE_2D_ARRAY,le,fe,K.width,K.height,K.depth),D)if(_.layerUpdates.size>0){const Z=th(K.width,K.height,_.format,_.type);for(const de of _.layerUpdates){const ve=K.data.subarray(de*Z/K.data.BYTES_PER_ELEMENT,(de+1)*Z/K.data.BYTES_PER_ELEMENT);t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,de,K.width,K.height,1,he,Pe,ve)}_.clearLayerUpdates()}else t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,K.width,K.height,K.depth,he,Pe,K.data)}else t.texImage3D(i.TEXTURE_2D_ARRAY,0,fe,K.width,K.height,K.depth,0,he,Pe,K.data);else if(_.isData3DTexture)Be?(qe&&t.texStorage3D(i.TEXTURE_3D,le,fe,K.width,K.height,K.depth),D&&t.texSubImage3D(i.TEXTURE_3D,0,0,0,0,K.width,K.height,K.depth,he,Pe,K.data)):t.texImage3D(i.TEXTURE_3D,0,fe,K.width,K.height,K.depth,0,he,Pe,K.data);else if(_.isFramebufferTexture){if(qe)if(Be)t.texStorage2D(i.TEXTURE_2D,le,fe,K.width,K.height);else{let Z=K.width,de=K.height;for(let ve=0;ve<le;ve++)t.texImage2D(i.TEXTURE_2D,ve,fe,Z,de,0,he,Pe,null),Z>>=1,de>>=1}}else if(_.isHTMLTexture){if("texElementImage2D"in i){const Z=i.canvas;if(Z.hasAttribute("layoutsubtree")||Z.setAttribute("layoutsubtree","true"),K.parentNode!==Z){Z.appendChild(K),d.add(_),Z.onpaint=de=>{const ve=de.changedElements;for(const ee of d)ve.includes(ee.image)&&(ee.needsUpdate=!0)},Z.requestPaint();return}if(i.texElementImage2D.length===3)i.texElementImage2D(i.TEXTURE_2D,i.RGBA8,K);else{const ve=i.RGBA,ee=i.RGBA,Ce=i.UNSIGNED_BYTE;i.texElementImage2D(i.TEXTURE_2D,0,ve,ee,Ce,K)}i.texParameteri(i.TEXTURE_2D,i.TEXTURE_MIN_FILTER,i.LINEAR),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_S,i.CLAMP_TO_EDGE),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_T,i.CLAMP_TO_EDGE)}}else if(Ue.length>0){if(Be&&qe){const Z=dt(Ue[0]);t.texStorage2D(i.TEXTURE_2D,le,fe,Z.width,Z.height)}for(let Z=0,de=Ue.length;Z<de;Z++)ue=Ue[Z],Be?D&&t.texSubImage2D(i.TEXTURE_2D,Z,0,0,he,Pe,ue):t.texImage2D(i.TEXTURE_2D,Z,fe,he,Pe,ue);_.generateMipmaps=!1}else if(Be){if(qe){const Z=dt(K);t.texStorage2D(i.TEXTURE_2D,le,fe,Z.width,Z.height)}D&&t.texSubImage2D(i.TEXTURE_2D,0,0,0,he,Pe,K)}else t.texImage2D(i.TEXTURE_2D,0,fe,he,Pe,K);f(_)&&M(z),ce.__version=re.version,_.onUpdate&&_.onUpdate(_)}A.__version=_.version}function Ve(A,_,O){if(_.image.length!==6)return;const z=Y(A,_),X=_.source;t.bindTexture(i.TEXTURE_CUBE_MAP,A.__webglTexture,i.TEXTURE0+O);const re=n.get(X);if(X.version!==re.__version||z===!0){t.activeTexture(i.TEXTURE0+O);const ce=et.getPrimaries(et.workingColorSpace),q=_.colorSpace===Gn?null:et.getPrimaries(_.colorSpace),K=_.colorSpace===Gn||ce===q?i.NONE:i.BROWSER_DEFAULT_WEBGL;t.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),t.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),t.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment),t.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,K);const he=_.isCompressedTexture||_.image[0].isCompressedTexture,Pe=_.image[0]&&_.image[0].isDataTexture,fe=[];for(let ee=0;ee<6;ee++)!he&&!Pe?fe[ee]=m(_.image[ee],!0,s.maxCubemapSize):fe[ee]=Pe?_.image[ee].image:_.image[ee],fe[ee]=en(_,fe[ee]);const ue=fe[0],Ue=r.convert(_.format,_.colorSpace),Be=r.convert(_.type),qe=y(_.internalFormat,Ue,Be,_.normalized,_.colorSpace),D=_.isVideoTexture!==!0,le=re.__version===void 0||z===!0,Z=X.dataReady;let de=S(_,ue);it(i.TEXTURE_CUBE_MAP,_);let ve;if(he){D&&le&&t.texStorage2D(i.TEXTURE_CUBE_MAP,de,qe,ue.width,ue.height);for(let ee=0;ee<6;ee++){ve=fe[ee].mipmaps;for(let Ce=0;Ce<ve.length;Ce++){const Te=ve[Ce];_.format!==gn?Ue!==null?D?Z&&t.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,Ce,0,0,Te.width,Te.height,Ue,Te.data):t.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,Ce,qe,Te.width,Te.height,0,Te.data):ke("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):D?Z&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,Ce,0,0,Te.width,Te.height,Ue,Be,Te.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,Ce,qe,Te.width,Te.height,0,Ue,Be,Te.data)}}}else{if(ve=_.mipmaps,D&&le){ve.length>0&&de++;const ee=dt(fe[0]);t.texStorage2D(i.TEXTURE_CUBE_MAP,de,qe,ee.width,ee.height)}for(let ee=0;ee<6;ee++)if(Pe){D?Z&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,0,0,0,fe[ee].width,fe[ee].height,Ue,Be,fe[ee].data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,0,qe,fe[ee].width,fe[ee].height,0,Ue,Be,fe[ee].data);for(let Ce=0;Ce<ve.length;Ce++){const Ct=ve[Ce].image[ee].image;D?Z&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,Ce+1,0,0,Ct.width,Ct.height,Ue,Be,Ct.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,Ce+1,qe,Ct.width,Ct.height,0,Ue,Be,Ct.data)}}else{D?Z&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,0,0,0,Ue,Be,fe[ee]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,0,qe,Ue,Be,fe[ee]);for(let Ce=0;Ce<ve.length;Ce++){const Te=ve[Ce];D?Z&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,Ce+1,0,0,Ue,Be,Te.image[ee]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ee,Ce+1,qe,Ue,Be,Te.image[ee])}}}f(_)&&M(i.TEXTURE_CUBE_MAP),re.__version=X.version,_.onUpdate&&_.onUpdate(_)}A.__version=_.version}function Ie(A,_,O,z,X,re){const ce=r.convert(O.format,O.colorSpace),q=r.convert(O.type),K=y(O.internalFormat,ce,q,O.normalized,O.colorSpace),he=n.get(_),Pe=n.get(O);if(Pe.__renderTarget=_,!he.__hasExternalTextures){const fe=Math.max(1,_.width>>re),ue=Math.max(1,_.height>>re);X===i.TEXTURE_3D||X===i.TEXTURE_2D_ARRAY?t.texImage3D(X,re,K,fe,ue,_.depth,0,ce,q,null):t.texImage2D(X,re,K,fe,ue,0,ce,q,null)}t.bindFramebuffer(i.FRAMEBUFFER,A),Nt(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,z,X,Pe.__webglTexture,0,Rt(_)):(X===i.TEXTURE_2D||X>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&X<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,z,X,Pe.__webglTexture,re),t.bindFramebuffer(i.FRAMEBUFFER,null)}function Et(A,_,O){if(i.bindRenderbuffer(i.RENDERBUFFER,A),_.depthBuffer){const z=_.depthTexture,X=z&&z.isDepthTexture?z.type:null,re=T(_.stencilBuffer,X),ce=_.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;Nt(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,Rt(_),re,_.width,_.height):O?i.renderbufferStorageMultisample(i.RENDERBUFFER,Rt(_),re,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,re,_.width,_.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,ce,i.RENDERBUFFER,A)}else{const z=_.textures;for(let X=0;X<z.length;X++){const re=z[X],ce=r.convert(re.format,re.colorSpace),q=r.convert(re.type),K=y(re.internalFormat,ce,q,re.normalized,re.colorSpace);Nt(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,Rt(_),K,_.width,_.height):O?i.renderbufferStorageMultisample(i.RENDERBUFFER,Rt(_),K,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,K,_.width,_.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function Je(A,_,O){const z=_.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(i.FRAMEBUFFER,A),!(_.depthTexture&&_.depthTexture.isDepthTexture))throw new Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");const X=n.get(_.depthTexture);if(X.__renderTarget=_,(!X.__webglTexture||_.depthTexture.image.width!==_.width||_.depthTexture.image.height!==_.height)&&(_.depthTexture.image.width=_.width,_.depthTexture.image.height=_.height,_.depthTexture.needsUpdate=!0),z){if(X.__webglInit===void 0&&(X.__webglInit=!0,_.depthTexture.addEventListener("dispose",R)),X.__webglTexture===void 0){X.__webglTexture=i.createTexture(),t.bindTexture(i.TEXTURE_CUBE_MAP,X.__webglTexture),it(i.TEXTURE_CUBE_MAP,_.depthTexture);const he=r.convert(_.depthTexture.format),Pe=r.convert(_.depthTexture.type);let fe;_.depthTexture.format===jn?fe=i.DEPTH_COMPONENT24:_.depthTexture.format===Ui&&(fe=i.DEPTH24_STENCIL8);for(let ue=0;ue<6;ue++)i.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ue,0,fe,_.width,_.height,0,he,Pe,null)}}else J(_.depthTexture,0);const re=X.__webglTexture,ce=Rt(_),q=z?i.TEXTURE_CUBE_MAP_POSITIVE_X+O:i.TEXTURE_2D,K=_.depthTexture.format===Ui?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;if(_.depthTexture.format===jn)Nt(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,K,q,re,0,ce):i.framebufferTexture2D(i.FRAMEBUFFER,K,q,re,0);else if(_.depthTexture.format===Ui)Nt(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,K,q,re,0,ce):i.framebufferTexture2D(i.FRAMEBUFFER,K,q,re,0);else throw new Error("THREE.WebGLTextures: Unknown depthTexture format.")}function j(A){const _=n.get(A),O=A.isWebGLCubeRenderTarget===!0;if(_.__boundDepthTexture!==A.depthTexture){const z=A.depthTexture;if(_.__depthDisposeCallback&&_.__depthDisposeCallback(),z){const X=()=>{delete _.__boundDepthTexture,delete _.__depthDisposeCallback,z.removeEventListener("dispose",X)};z.addEventListener("dispose",X),_.__depthDisposeCallback=X}_.__boundDepthTexture=z}if(A.depthTexture&&!_.__autoAllocateDepthBuffer)if(O)for(let z=0;z<6;z++)Je(_.__webglFramebuffer[z],A,z);else{const z=A.texture.mipmaps;z&&z.length>0?Je(_.__webglFramebuffer[0],A,0):Je(_.__webglFramebuffer,A,0)}else if(O){_.__webglDepthbuffer=[];for(let z=0;z<6;z++)if(t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[z]),_.__webglDepthbuffer[z]===void 0)_.__webglDepthbuffer[z]=i.createRenderbuffer(),Et(_.__webglDepthbuffer[z],A,!1);else{const X=A.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,re=_.__webglDepthbuffer[z];i.bindRenderbuffer(i.RENDERBUFFER,re),i.framebufferRenderbuffer(i.FRAMEBUFFER,X,i.RENDERBUFFER,re)}}else{const z=A.texture.mipmaps;if(z&&z.length>0?t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[0]):t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer),_.__webglDepthbuffer===void 0)_.__webglDepthbuffer=i.createRenderbuffer(),Et(_.__webglDepthbuffer,A,!1);else{const X=A.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,re=_.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,re),i.framebufferRenderbuffer(i.FRAMEBUFFER,X,i.RENDERBUFFER,re)}}t.bindFramebuffer(i.FRAMEBUFFER,null)}function Ne(A,_,O){const z=n.get(A);_!==void 0&&Ie(z.__webglFramebuffer,A,A.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),O!==void 0&&j(A)}function ze(A){const _=A.texture,O=n.get(A),z=n.get(_);A.addEventListener("dispose",v);const X=A.textures,re=A.isWebGLCubeRenderTarget===!0,ce=X.length>1;if(ce||(z.__webglTexture===void 0&&(z.__webglTexture=i.createTexture()),z.__version=_.version,a.memory.textures++),re){O.__webglFramebuffer=[];for(let q=0;q<6;q++)if(_.mipmaps&&_.mipmaps.length>0){O.__webglFramebuffer[q]=[];for(let K=0;K<_.mipmaps.length;K++)O.__webglFramebuffer[q][K]=i.createFramebuffer()}else O.__webglFramebuffer[q]=i.createFramebuffer()}else{if(_.mipmaps&&_.mipmaps.length>0){O.__webglFramebuffer=[];for(let q=0;q<_.mipmaps.length;q++)O.__webglFramebuffer[q]=i.createFramebuffer()}else O.__webglFramebuffer=i.createFramebuffer();if(ce)for(let q=0,K=X.length;q<K;q++){const he=n.get(X[q]);he.__webglTexture===void 0&&(he.__webglTexture=i.createTexture(),a.memory.textures++)}if(A.samples>0&&Nt(A)===!1){O.__webglMultisampledFramebuffer=i.createFramebuffer(),O.__webglColorRenderbuffer=[],t.bindFramebuffer(i.FRAMEBUFFER,O.__webglMultisampledFramebuffer);for(let q=0;q<X.length;q++){const K=X[q];O.__webglColorRenderbuffer[q]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,O.__webglColorRenderbuffer[q]);const he=r.convert(K.format,K.colorSpace),Pe=r.convert(K.type),fe=y(K.internalFormat,he,Pe,K.normalized,K.colorSpace,A.isXRRenderTarget===!0),ue=Rt(A);i.renderbufferStorageMultisample(i.RENDERBUFFER,ue,fe,A.width,A.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+q,i.RENDERBUFFER,O.__webglColorRenderbuffer[q])}i.bindRenderbuffer(i.RENDERBUFFER,null),A.depthBuffer&&(O.__webglDepthRenderbuffer=i.createRenderbuffer(),Et(O.__webglDepthRenderbuffer,A,!0)),t.bindFramebuffer(i.FRAMEBUFFER,null)}}if(re){t.bindTexture(i.TEXTURE_CUBE_MAP,z.__webglTexture),it(i.TEXTURE_CUBE_MAP,_);for(let q=0;q<6;q++)if(_.mipmaps&&_.mipmaps.length>0)for(let K=0;K<_.mipmaps.length;K++)Ie(O.__webglFramebuffer[q][K],A,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+q,K);else Ie(O.__webglFramebuffer[q],A,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+q,0);f(_)&&M(i.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(ce){for(let q=0,K=X.length;q<K;q++){const he=X[q],Pe=n.get(he);let fe=i.TEXTURE_2D;(A.isWebGL3DRenderTarget||A.isWebGLArrayRenderTarget)&&(fe=A.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(fe,Pe.__webglTexture),it(fe,he),Ie(O.__webglFramebuffer,A,he,i.COLOR_ATTACHMENT0+q,fe,0),f(he)&&M(fe)}t.unbindTexture()}else{let q=i.TEXTURE_2D;if((A.isWebGL3DRenderTarget||A.isWebGLArrayRenderTarget)&&(q=A.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(q,z.__webglTexture),it(q,_),_.mipmaps&&_.mipmaps.length>0)for(let K=0;K<_.mipmaps.length;K++)Ie(O.__webglFramebuffer[K],A,_,i.COLOR_ATTACHMENT0,q,K);else Ie(O.__webglFramebuffer,A,_,i.COLOR_ATTACHMENT0,q,0);f(_)&&M(q),t.unbindTexture()}A.depthBuffer&&j(A)}function ut(A){const _=A.textures;for(let O=0,z=_.length;O<z;O++){const X=_[O];if(f(X)){const re=E(A),ce=n.get(X).__webglTexture;t.bindTexture(re,ce),M(re),t.unbindTexture()}}}const xt=[],It=[];function $t(A){if(A.samples>0){if(Nt(A)===!1){const _=A.textures,O=A.width,z=A.height;let X=i.COLOR_BUFFER_BIT;const re=A.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,ce=n.get(A),q=_.length>1;if(q)for(let he=0;he<_.length;he++)t.bindFramebuffer(i.FRAMEBUFFER,ce.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+he,i.RENDERBUFFER,null),t.bindFramebuffer(i.FRAMEBUFFER,ce.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+he,i.TEXTURE_2D,null,0);t.bindFramebuffer(i.READ_FRAMEBUFFER,ce.__webglMultisampledFramebuffer);const K=A.texture.mipmaps;K&&K.length>0?t.bindFramebuffer(i.DRAW_FRAMEBUFFER,ce.__webglFramebuffer[0]):t.bindFramebuffer(i.DRAW_FRAMEBUFFER,ce.__webglFramebuffer);for(let he=0;he<_.length;he++){if(A.resolveDepthBuffer&&(A.depthBuffer&&(X|=i.DEPTH_BUFFER_BIT),A.stencilBuffer&&A.resolveStencilBuffer&&(X|=i.STENCIL_BUFFER_BIT)),q){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,ce.__webglColorRenderbuffer[he]);const Pe=n.get(_[he]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,Pe,0)}i.blitFramebuffer(0,0,O,z,0,0,O,z,X,i.NEAREST),l===!0&&(xt.length=0,It.length=0,xt.push(i.COLOR_ATTACHMENT0+he),A.depthBuffer&&A.resolveDepthBuffer===!1&&(xt.push(re),It.push(re),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,It)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,xt))}if(t.bindFramebuffer(i.READ_FRAMEBUFFER,null),t.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),q)for(let he=0;he<_.length;he++){t.bindFramebuffer(i.FRAMEBUFFER,ce.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+he,i.RENDERBUFFER,ce.__webglColorRenderbuffer[he]);const Pe=n.get(_[he]).__webglTexture;t.bindFramebuffer(i.FRAMEBUFFER,ce.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+he,i.TEXTURE_2D,Pe,0)}t.bindFramebuffer(i.DRAW_FRAMEBUFFER,ce.__webglMultisampledFramebuffer)}else if(A.depthBuffer&&A.resolveDepthBuffer===!1&&l){const _=A.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[_])}}}function Rt(A){return Math.min(s.maxSamples,A.samples)}function Nt(A){const _=n.get(A);return A.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&_.__useRenderToTexture!==!1}function I(A){const _=a.render.frame;h.get(A)!==_&&(h.set(A,_),A.update())}function en(A,_){const O=A.colorSpace,z=A.format,X=A.type;return A.isCompressedTexture===!0||A.isVideoTexture===!0||O!==oa&&O!==Gn&&(et.getTransfer(O)===ft?(z!==gn||X!==hn)&&ke("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):st("WebGLTextures: Unsupported texture color space:",O)),_}function dt(A){return typeof HTMLImageElement<"u"&&A instanceof HTMLImageElement?(c.width=A.naturalWidth||A.width,c.height=A.naturalHeight||A.height):typeof VideoFrame<"u"&&A instanceof VideoFrame?(c.width=A.displayWidth,c.height=A.displayHeight):(c.width=A.width,c.height=A.height),c}this.allocateTextureUnit=W,this.resetTextureUnits=V,this.getTextureUnits=$,this.setTextureUnits=F,this.setTexture2D=J,this.setTexture2DArray=te,this.setTexture3D=oe,this.setTextureCube=me,this.rebindTextures=Ne,this.setupRenderTarget=ze,this.updateRenderTargetMipmap=ut,this.updateMultisampleRenderTarget=$t,this.setupDepthRenderbuffer=j,this.setupFrameBufferTexture=Ie,this.useMultisampledRTT=Nt,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function rv(i,e){function t(n,s=Gn){let r;const a=et.getTransfer(s);if(n===hn)return i.UNSIGNED_BYTE;if(n===Dl)return i.UNSIGNED_SHORT_4_4_4_4;if(n===Il)return i.UNSIGNED_SHORT_5_5_5_1;if(n===Bu)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===zu)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===Fu)return i.BYTE;if(n===ku)return i.SHORT;if(n===nr)return i.UNSIGNED_SHORT;if(n===Ll)return i.INT;if(n===On)return i.UNSIGNED_INT;if(n===bn)return i.FLOAT;if(n===Kn)return i.HALF_FLOAT;if(n===Hu)return i.ALPHA;if(n===Vu)return i.RGB;if(n===gn)return i.RGBA;if(n===jn)return i.DEPTH_COMPONENT;if(n===Ui)return i.DEPTH_STENCIL;if(n===lr)return i.RED;if(n===Nl)return i.RED_INTEGER;if(n===ki)return i.RG;if(n===Ul)return i.RG_INTEGER;if(n===Ol)return i.RGBA_INTEGER;if(n===Qr||n===ea||n===ta||n===na)if(a===ft)if(r=e.get("WEBGL_compressed_texture_s3tc_srgb"),r!==null){if(n===Qr)return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===ea)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===ta)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===na)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(r=e.get("WEBGL_compressed_texture_s3tc"),r!==null){if(n===Qr)return r.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===ea)return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===ta)return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===na)return r.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===Uo||n===Oo||n===Fo||n===ko)if(r=e.get("WEBGL_compressed_texture_pvrtc"),r!==null){if(n===Uo)return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===Oo)return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===Fo)return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===ko)return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===Bo||n===zo||n===Ho||n===Vo||n===Go||n===ra||n===Wo)if(r=e.get("WEBGL_compressed_texture_etc"),r!==null){if(n===Bo||n===zo)return a===ft?r.COMPRESSED_SRGB8_ETC2:r.COMPRESSED_RGB8_ETC2;if(n===Ho)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:r.COMPRESSED_RGBA8_ETC2_EAC;if(n===Vo)return r.COMPRESSED_R11_EAC;if(n===Go)return r.COMPRESSED_SIGNED_R11_EAC;if(n===ra)return r.COMPRESSED_RG11_EAC;if(n===Wo)return r.COMPRESSED_SIGNED_RG11_EAC}else return null;if(n===$o||n===Xo||n===qo||n===Yo||n===Zo||n===Ko||n===jo||n===Jo||n===Qo||n===el||n===tl||n===nl||n===il||n===sl)if(r=e.get("WEBGL_compressed_texture_astc"),r!==null){if(n===$o)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:r.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===Xo)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:r.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===qo)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:r.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===Yo)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:r.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===Zo)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:r.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===Ko)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:r.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===jo)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:r.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===Jo)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:r.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===Qo)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:r.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===el)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:r.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===tl)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:r.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===nl)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:r.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===il)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:r.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===sl)return a===ft?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:r.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===rl||n===al||n===ol)if(r=e.get("EXT_texture_compression_bptc"),r!==null){if(n===rl)return a===ft?r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:r.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===al)return r.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===ol)return r.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===ll||n===cl||n===aa||n===hl)if(r=e.get("EXT_texture_compression_rgtc"),r!==null){if(n===ll)return r.COMPRESSED_RED_RGTC1_EXT;if(n===cl)return r.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===aa)return r.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===hl)return r.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===ir?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:t}}const av=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,ov=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class lv{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){const n=new ju(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=n}}getMesh(e){if(this.texture!==null&&this.mesh===null){const t=e.cameras[0].viewport,n=new En({vertexShader:av,fragmentShader:ov,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new ht(new un(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class cv extends Ei{constructor(e,t){super();const n=this;let s=null,r=1,a=null,o="local-floor",l=1,c=null,h=null,d=null,u=null,p=null,g=null;const x=typeof XRWebGLBinding<"u",m=new lv,f={},M=t.getContextAttributes();let E=null,y=null;const T=[],S=[],R=new Fe;let v=null;const w=new cn;w.viewport=new At;const C=new cn;C.viewport=new At;const L=[w,C],N=new _p;let V=null,$=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(Y){let ae=T[Y];return ae===void 0&&(ae=new ka,T[Y]=ae),ae.getTargetRaySpace()},this.getControllerGrip=function(Y){let ae=T[Y];return ae===void 0&&(ae=new ka,T[Y]=ae),ae.getGripSpace()},this.getHand=function(Y){let ae=T[Y];return ae===void 0&&(ae=new ka,T[Y]=ae),ae.getHandSpace()};function F(Y){const ae=S.indexOf(Y.inputSource);if(ae===-1)return;const ne=T[ae];ne!==void 0&&(ne.update(Y.inputSource,Y.frame,c||a),ne.dispatchEvent({type:Y.type,data:Y.inputSource}))}function W(){s.removeEventListener("select",F),s.removeEventListener("selectstart",F),s.removeEventListener("selectend",F),s.removeEventListener("squeeze",F),s.removeEventListener("squeezestart",F),s.removeEventListener("squeezeend",F),s.removeEventListener("end",W),s.removeEventListener("inputsourceschange",G);for(let Y=0;Y<T.length;Y++){const ae=S[Y];ae!==null&&(S[Y]=null,T[Y].disconnect(ae))}V=null,$=null,m.reset();for(const Y in f)delete f[Y];e.setRenderTarget(E),p=null,u=null,d=null,s=null,y=null,it.stop(),n.isPresenting=!1,e.setPixelRatio(v),e.setSize(R.width,R.height,!1),n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(Y){r=Y,n.isPresenting===!0&&ke("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(Y){o=Y,n.isPresenting===!0&&ke("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(Y){c=Y},this.getBaseLayer=function(){return u!==null?u:p},this.getBinding=function(){return d===null&&x&&(d=new XRWebGLBinding(s,t)),d},this.getFrame=function(){return g},this.getSession=function(){return s},this.setSession=async function(Y){if(s=Y,s!==null){if(E=e.getRenderTarget(),s.addEventListener("select",F),s.addEventListener("selectstart",F),s.addEventListener("selectend",F),s.addEventListener("squeeze",F),s.addEventListener("squeezestart",F),s.addEventListener("squeezeend",F),s.addEventListener("end",W),s.addEventListener("inputsourceschange",G),M.xrCompatible!==!0&&await t.makeXRCompatible(),v=e.getPixelRatio(),e.getSize(R),x&&"createProjectionLayer"in XRWebGLBinding.prototype){let ne=null,Oe=null,Ve=null;M.depth&&(Ve=M.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,ne=M.stencil?Ui:jn,Oe=M.stencil?ir:On);const Ie={colorFormat:t.RGBA8,depthFormat:Ve,scaleFactor:r};d=this.getBinding(),u=d.createProjectionLayer(Ie),s.updateRenderState({layers:[u]}),e.setPixelRatio(1),e.setSize(u.textureWidth,u.textureHeight,!1),y=new Nn(u.textureWidth,u.textureHeight,{format:gn,type:hn,depthTexture:new Ms(u.textureWidth,u.textureHeight,Oe,void 0,void 0,void 0,void 0,void 0,void 0,ne),stencilBuffer:M.stencil,colorSpace:e.outputColorSpace,samples:M.antialias?4:0,resolveDepthBuffer:u.ignoreDepthValues===!1,resolveStencilBuffer:u.ignoreDepthValues===!1})}else{const ne={antialias:M.antialias,alpha:!0,depth:M.depth,stencil:M.stencil,framebufferScaleFactor:r};p=new XRWebGLLayer(s,t,ne),s.updateRenderState({baseLayer:p}),e.setPixelRatio(1),e.setSize(p.framebufferWidth,p.framebufferHeight,!1),y=new Nn(p.framebufferWidth,p.framebufferHeight,{format:gn,type:hn,colorSpace:e.outputColorSpace,stencilBuffer:M.stencil,resolveDepthBuffer:p.ignoreDepthValues===!1,resolveStencilBuffer:p.ignoreDepthValues===!1})}y.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await s.requestReferenceSpace(o),it.setContext(s),it.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(s!==null)return s.environmentBlendMode},this.getDepthTexture=function(){return m.getDepthTexture()};function G(Y){for(let ae=0;ae<Y.removed.length;ae++){const ne=Y.removed[ae],Oe=S.indexOf(ne);Oe>=0&&(S[Oe]=null,T[Oe].disconnect(ne))}for(let ae=0;ae<Y.added.length;ae++){const ne=Y.added[ae];let Oe=S.indexOf(ne);if(Oe===-1){for(let Ie=0;Ie<T.length;Ie++)if(Ie>=S.length){S.push(ne),Oe=Ie;break}else if(S[Ie]===null){S[Ie]=ne,Oe=Ie;break}if(Oe===-1)break}const Ve=T[Oe];Ve&&Ve.connect(ne)}}const J=new P,te=new P;function oe(Y,ae,ne){J.setFromMatrixPosition(ae.matrixWorld),te.setFromMatrixPosition(ne.matrixWorld);const Oe=J.distanceTo(te),Ve=ae.projectionMatrix.elements,Ie=ne.projectionMatrix.elements,Et=Ve[14]/(Ve[10]-1),Je=Ve[14]/(Ve[10]+1),j=(Ve[9]+1)/Ve[5],Ne=(Ve[9]-1)/Ve[5],ze=(Ve[8]-1)/Ve[0],ut=(Ie[8]+1)/Ie[0],xt=Et*ze,It=Et*ut,$t=Oe/(-ze+ut),Rt=$t*-ze;if(ae.matrixWorld.decompose(Y.position,Y.quaternion,Y.scale),Y.translateX(Rt),Y.translateZ($t),Y.matrixWorld.compose(Y.position,Y.quaternion,Y.scale),Y.matrixWorldInverse.copy(Y.matrixWorld).invert(),Ve[10]===-1)Y.projectionMatrix.copy(ae.projectionMatrix),Y.projectionMatrixInverse.copy(ae.projectionMatrixInverse);else{const Nt=Et+$t,I=Je+$t,en=xt-Rt,dt=It+(Oe-Rt),A=j*Je/I*Nt,_=Ne*Je/I*Nt;Y.projectionMatrix.makePerspective(en,dt,A,_,Nt,I),Y.projectionMatrixInverse.copy(Y.projectionMatrix).invert()}}function me(Y,ae){ae===null?Y.matrixWorld.copy(Y.matrix):Y.matrixWorld.multiplyMatrices(ae.matrixWorld,Y.matrix),Y.matrixWorldInverse.copy(Y.matrixWorld).invert()}this.updateCamera=function(Y){if(s===null)return;let ae=Y.near,ne=Y.far;m.texture!==null&&(m.depthNear>0&&(ae=m.depthNear),m.depthFar>0&&(ne=m.depthFar)),N.near=C.near=w.near=ae,N.far=C.far=w.far=ne,(V!==N.near||$!==N.far)&&(s.updateRenderState({depthNear:N.near,depthFar:N.far}),V=N.near,$=N.far),N.layers.mask=Y.layers.mask|6,w.layers.mask=N.layers.mask&-5,C.layers.mask=N.layers.mask&-3;const Oe=Y.parent,Ve=N.cameras;me(N,Oe);for(let Ie=0;Ie<Ve.length;Ie++)me(Ve[Ie],Oe);Ve.length===2?oe(N,w,C):N.projectionMatrix.copy(w.projectionMatrix),be(Y,N,Oe)};function be(Y,ae,ne){ne===null?Y.matrix.copy(ae.matrixWorld):(Y.matrix.copy(ne.matrixWorld),Y.matrix.invert(),Y.matrix.multiply(ae.matrixWorld)),Y.matrix.decompose(Y.position,Y.quaternion,Y.scale),Y.updateMatrixWorld(!0),Y.projectionMatrix.copy(ae.projectionMatrix),Y.projectionMatrixInverse.copy(ae.projectionMatrixInverse),Y.isPerspectiveCamera&&(Y.fov=dl*2*Math.atan(1/Y.projectionMatrix.elements[5]),Y.zoom=1)}this.getCamera=function(){return N},this.getFoveation=function(){if(!(u===null&&p===null))return l},this.setFoveation=function(Y){l=Y,u!==null&&(u.fixedFoveation=Y),p!==null&&p.fixedFoveation!==void 0&&(p.fixedFoveation=Y)},this.hasDepthSensing=function(){return m.texture!==null},this.getDepthSensingMesh=function(){return m.getMesh(N)},this.getCameraTexture=function(Y){return f[Y]};let at=null;function gt(Y,ae){if(h=ae.getViewerPose(c||a),g=ae,h!==null){const ne=h.views;p!==null&&(e.setRenderTargetFramebuffer(y,p.framebuffer),e.setRenderTarget(y));let Oe=!1;ne.length!==N.cameras.length&&(N.cameras.length=0,Oe=!0);for(let Je=0;Je<ne.length;Je++){const j=ne[Je];let Ne=null;if(p!==null)Ne=p.getViewport(j);else{const ut=d.getViewSubImage(u,j);Ne=ut.viewport,Je===0&&(e.setRenderTargetTextures(y,ut.colorTexture,ut.depthStencilTexture),e.setRenderTarget(y))}let ze=L[Je];ze===void 0&&(ze=new cn,ze.layers.enable(Je),ze.viewport=new At,L[Je]=ze),ze.matrix.fromArray(j.transform.matrix),ze.matrix.decompose(ze.position,ze.quaternion,ze.scale),ze.projectionMatrix.fromArray(j.projectionMatrix),ze.projectionMatrixInverse.copy(ze.projectionMatrix).invert(),ze.viewport.set(Ne.x,Ne.y,Ne.width,Ne.height),Je===0&&(N.matrix.copy(ze.matrix),N.matrix.decompose(N.position,N.quaternion,N.scale)),Oe===!0&&N.cameras.push(ze)}const Ve=s.enabledFeatures;if(Ve&&Ve.includes("depth-sensing")&&s.depthUsage=="gpu-optimized"&&x){d=n.getBinding();const Je=d.getDepthInformation(ne[0]);Je&&Je.isValid&&Je.texture&&m.init(Je,s.renderState)}if(Ve&&Ve.includes("camera-access")&&x){e.state.unbindTexture(),d=n.getBinding();for(let Je=0;Je<ne.length;Je++){const j=ne[Je].camera;if(j){let Ne=f[j];Ne||(Ne=new ju,f[j]=Ne);const ze=d.getCameraImage(j);Ne.sourceTexture=ze}}}}for(let ne=0;ne<T.length;ne++){const Oe=S[ne],Ve=T[ne];Oe!==null&&Ve!==void 0&&Ve.update(Oe,ae,c||a)}at&&at(Y,ae),ae.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:ae}),g=null}const it=new id;it.setAnimationLoop(gt),this.setAnimationLoop=function(Y){at=Y},this.dispose=function(){}}}const hv=new He,hd=new Xe;hd.set(-1,0,0,0,1,0,0,0,1);function uv(i,e){function t(m,f){m.matrixAutoUpdate===!0&&m.updateMatrix(),f.value.copy(m.matrix)}function n(m,f){f.color.getRGB(m.fogColor.value,Qu(i)),f.isFog?(m.fogNear.value=f.near,m.fogFar.value=f.far):f.isFogExp2&&(m.fogDensity.value=f.density)}function s(m,f,M,E,y){f.isNodeMaterial?f.uniformsNeedUpdate=!1:f.isMeshBasicMaterial?r(m,f):f.isMeshLambertMaterial?(r(m,f),f.envMap&&(m.envMapIntensity.value=f.envMapIntensity)):f.isMeshToonMaterial?(r(m,f),d(m,f)):f.isMeshPhongMaterial?(r(m,f),h(m,f),f.envMap&&(m.envMapIntensity.value=f.envMapIntensity)):f.isMeshStandardMaterial?(r(m,f),u(m,f),f.isMeshPhysicalMaterial&&p(m,f,y)):f.isMeshMatcapMaterial?(r(m,f),g(m,f)):f.isMeshDepthMaterial?r(m,f):f.isMeshDistanceMaterial?(r(m,f),x(m,f)):f.isMeshNormalMaterial?r(m,f):f.isLineBasicMaterial?(a(m,f),f.isLineDashedMaterial&&o(m,f)):f.isPointsMaterial?l(m,f,M,E):f.isSpriteMaterial?c(m,f):f.isShadowMaterial?(m.color.value.copy(f.color),m.opacity.value=f.opacity):f.isShaderMaterial&&(f.uniformsNeedUpdate=!1)}function r(m,f){m.opacity.value=f.opacity,f.color&&m.diffuse.value.copy(f.color),f.emissive&&m.emissive.value.copy(f.emissive).multiplyScalar(f.emissiveIntensity),f.map&&(m.map.value=f.map,t(f.map,m.mapTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.bumpMap&&(m.bumpMap.value=f.bumpMap,t(f.bumpMap,m.bumpMapTransform),m.bumpScale.value=f.bumpScale,f.side===rn&&(m.bumpScale.value*=-1)),f.normalMap&&(m.normalMap.value=f.normalMap,t(f.normalMap,m.normalMapTransform),m.normalScale.value.copy(f.normalScale),f.side===rn&&m.normalScale.value.negate()),f.displacementMap&&(m.displacementMap.value=f.displacementMap,t(f.displacementMap,m.displacementMapTransform),m.displacementScale.value=f.displacementScale,m.displacementBias.value=f.displacementBias),f.emissiveMap&&(m.emissiveMap.value=f.emissiveMap,t(f.emissiveMap,m.emissiveMapTransform)),f.specularMap&&(m.specularMap.value=f.specularMap,t(f.specularMap,m.specularMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest);const M=e.get(f),E=M.envMap,y=M.envMapRotation;E&&(m.envMap.value=E,m.envMapRotation.value.setFromMatrix4(hv.makeRotationFromEuler(y)).transpose(),E.isCubeTexture&&E.isRenderTargetTexture===!1&&m.envMapRotation.value.premultiply(hd),m.reflectivity.value=f.reflectivity,m.ior.value=f.ior,m.refractionRatio.value=f.refractionRatio),f.lightMap&&(m.lightMap.value=f.lightMap,m.lightMapIntensity.value=f.lightMapIntensity,t(f.lightMap,m.lightMapTransform)),f.aoMap&&(m.aoMap.value=f.aoMap,m.aoMapIntensity.value=f.aoMapIntensity,t(f.aoMap,m.aoMapTransform))}function a(m,f){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,f.map&&(m.map.value=f.map,t(f.map,m.mapTransform))}function o(m,f){m.dashSize.value=f.dashSize,m.totalSize.value=f.dashSize+f.gapSize,m.scale.value=f.scale}function l(m,f,M,E){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,m.size.value=f.size*M,m.scale.value=E*.5,f.map&&(m.map.value=f.map,t(f.map,m.uvTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest)}function c(m,f){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,m.rotation.value=f.rotation,f.map&&(m.map.value=f.map,t(f.map,m.mapTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest)}function h(m,f){m.specular.value.copy(f.specular),m.shininess.value=Math.max(f.shininess,1e-4)}function d(m,f){f.gradientMap&&(m.gradientMap.value=f.gradientMap)}function u(m,f){m.metalness.value=f.metalness,f.metalnessMap&&(m.metalnessMap.value=f.metalnessMap,t(f.metalnessMap,m.metalnessMapTransform)),m.roughness.value=f.roughness,f.roughnessMap&&(m.roughnessMap.value=f.roughnessMap,t(f.roughnessMap,m.roughnessMapTransform)),f.envMap&&(m.envMapIntensity.value=f.envMapIntensity)}function p(m,f,M){m.ior.value=f.ior,f.sheen>0&&(m.sheenColor.value.copy(f.sheenColor).multiplyScalar(f.sheen),m.sheenRoughness.value=f.sheenRoughness,f.sheenColorMap&&(m.sheenColorMap.value=f.sheenColorMap,t(f.sheenColorMap,m.sheenColorMapTransform)),f.sheenRoughnessMap&&(m.sheenRoughnessMap.value=f.sheenRoughnessMap,t(f.sheenRoughnessMap,m.sheenRoughnessMapTransform))),f.clearcoat>0&&(m.clearcoat.value=f.clearcoat,m.clearcoatRoughness.value=f.clearcoatRoughness,f.clearcoatMap&&(m.clearcoatMap.value=f.clearcoatMap,t(f.clearcoatMap,m.clearcoatMapTransform)),f.clearcoatRoughnessMap&&(m.clearcoatRoughnessMap.value=f.clearcoatRoughnessMap,t(f.clearcoatRoughnessMap,m.clearcoatRoughnessMapTransform)),f.clearcoatNormalMap&&(m.clearcoatNormalMap.value=f.clearcoatNormalMap,t(f.clearcoatNormalMap,m.clearcoatNormalMapTransform),m.clearcoatNormalScale.value.copy(f.clearcoatNormalScale),f.side===rn&&m.clearcoatNormalScale.value.negate())),f.dispersion>0&&(m.dispersion.value=f.dispersion),f.iridescence>0&&(m.iridescence.value=f.iridescence,m.iridescenceIOR.value=f.iridescenceIOR,m.iridescenceThicknessMinimum.value=f.iridescenceThicknessRange[0],m.iridescenceThicknessMaximum.value=f.iridescenceThicknessRange[1],f.iridescenceMap&&(m.iridescenceMap.value=f.iridescenceMap,t(f.iridescenceMap,m.iridescenceMapTransform)),f.iridescenceThicknessMap&&(m.iridescenceThicknessMap.value=f.iridescenceThicknessMap,t(f.iridescenceThicknessMap,m.iridescenceThicknessMapTransform))),f.transmission>0&&(m.transmission.value=f.transmission,m.transmissionSamplerMap.value=M.texture,m.transmissionSamplerSize.value.set(M.width,M.height),f.transmissionMap&&(m.transmissionMap.value=f.transmissionMap,t(f.transmissionMap,m.transmissionMapTransform)),m.thickness.value=f.thickness,f.thicknessMap&&(m.thicknessMap.value=f.thicknessMap,t(f.thicknessMap,m.thicknessMapTransform)),m.attenuationDistance.value=f.attenuationDistance,m.attenuationColor.value.copy(f.attenuationColor)),f.anisotropy>0&&(m.anisotropyVector.value.set(f.anisotropy*Math.cos(f.anisotropyRotation),f.anisotropy*Math.sin(f.anisotropyRotation)),f.anisotropyMap&&(m.anisotropyMap.value=f.anisotropyMap,t(f.anisotropyMap,m.anisotropyMapTransform))),m.specularIntensity.value=f.specularIntensity,m.specularColor.value.copy(f.specularColor),f.specularColorMap&&(m.specularColorMap.value=f.specularColorMap,t(f.specularColorMap,m.specularColorMapTransform)),f.specularIntensityMap&&(m.specularIntensityMap.value=f.specularIntensityMap,t(f.specularIntensityMap,m.specularIntensityMapTransform))}function g(m,f){f.matcap&&(m.matcap.value=f.matcap)}function x(m,f){const M=e.get(f).light;m.referencePosition.value.setFromMatrixPosition(M.matrixWorld),m.nearDistance.value=M.shadow.camera.near,m.farDistance.value=M.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:s}}function dv(i,e,t,n){let s={},r={},a=[];const o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function l(y,T){const S=T.program;n.uniformBlockBinding(y,S)}function c(y,T){let S=s[y.id];S===void 0&&(m(y),S=h(y),s[y.id]=S,y.addEventListener("dispose",M));const R=T.program;n.updateUBOMapping(y,R);const v=e.render.frame;r[y.id]!==v&&(u(y),r[y.id]=v)}function h(y){const T=d();y.__bindingPointIndex=T;const S=i.createBuffer(),R=y.__size,v=y.usage;return i.bindBuffer(i.UNIFORM_BUFFER,S),i.bufferData(i.UNIFORM_BUFFER,R,v),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,T,S),S}function d(){for(let y=0;y<o;y++)if(a.indexOf(y)===-1)return a.push(y),y;return st("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function u(y){const T=s[y.id],S=y.uniforms,R=y.__cache;i.bindBuffer(i.UNIFORM_BUFFER,T);for(let v=0,w=S.length;v<w;v++){const C=S[v];if(Array.isArray(C))for(let L=0,N=C.length;L<N;L++)p(C[L],v,L,R);else p(C,v,0,R)}i.bindBuffer(i.UNIFORM_BUFFER,null)}function p(y,T,S,R){if(x(y,T,S,R)===!0){const v=y.__offset,w=y.value;if(Array.isArray(w)){let C=0;for(let L=0;L<w.length;L++){const N=w[L],V=f(N);g(N,y.__data,C),typeof N!="number"&&typeof N!="boolean"&&!N.isMatrix3&&!ArrayBuffer.isView(N)&&(C+=V.storage/Float32Array.BYTES_PER_ELEMENT)}}else g(w,y.__data,0);i.bufferSubData(i.UNIFORM_BUFFER,v,y.__data)}}function g(y,T,S){typeof y=="number"||typeof y=="boolean"?T[0]=y:y.isMatrix3?(T[0]=y.elements[0],T[1]=y.elements[1],T[2]=y.elements[2],T[3]=0,T[4]=y.elements[3],T[5]=y.elements[4],T[6]=y.elements[5],T[7]=0,T[8]=y.elements[6],T[9]=y.elements[7],T[10]=y.elements[8],T[11]=0):ArrayBuffer.isView(y)?T.set(new y.constructor(y.buffer,y.byteOffset,T.length)):y.toArray(T,S)}function x(y,T,S,R){const v=y.value,w=T+"_"+S;if(R[w]===void 0)return typeof v=="number"||typeof v=="boolean"?R[w]=v:ArrayBuffer.isView(v)?R[w]=v.slice():R[w]=v.clone(),!0;{const C=R[w];if(typeof v=="number"||typeof v=="boolean"){if(C!==v)return R[w]=v,!0}else{if(ArrayBuffer.isView(v))return!0;if(C.equals(v)===!1)return C.copy(v),!0}}return!1}function m(y){const T=y.uniforms;let S=0;const R=16;for(let w=0,C=T.length;w<C;w++){const L=Array.isArray(T[w])?T[w]:[T[w]];for(let N=0,V=L.length;N<V;N++){const $=L[N],F=Array.isArray($.value)?$.value:[$.value];for(let W=0,G=F.length;W<G;W++){const J=F[W],te=f(J),oe=S%R,me=oe%te.boundary,be=oe+me;S+=me,be!==0&&R-be<te.storage&&(S+=R-be),$.__data=new Float32Array(te.storage/Float32Array.BYTES_PER_ELEMENT),$.__offset=S,S+=te.storage}}}const v=S%R;return v>0&&(S+=R-v),y.__size=S,y.__cache={},this}function f(y){const T={boundary:0,storage:0};return typeof y=="number"||typeof y=="boolean"?(T.boundary=4,T.storage=4):y.isVector2?(T.boundary=8,T.storage=8):y.isVector3||y.isColor?(T.boundary=16,T.storage=12):y.isVector4?(T.boundary=16,T.storage=16):y.isMatrix3?(T.boundary=48,T.storage=48):y.isMatrix4?(T.boundary=64,T.storage=64):y.isTexture?ke("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(y)?(T.boundary=16,T.storage=y.byteLength):ke("WebGLRenderer: Unsupported uniform value type.",y),T}function M(y){const T=y.target;T.removeEventListener("dispose",M);const S=a.indexOf(T.__bindingPointIndex);a.splice(S,1),i.deleteBuffer(s[T.id]),delete s[T.id],delete r[T.id]}function E(){for(const y in s)i.deleteBuffer(s[y]);a=[],s={},r={}}return{bind:l,update:c,dispose:E}}const fv=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);let Cn=null;function pv(){return Cn===null&&(Cn=new hr(fv,16,16,ki,Kn),Cn.name="DFG_LUT",Cn.minFilter=Zt,Cn.magFilter=Zt,Cn.wrapS=Wn,Cn.wrapT=Wn,Cn.generateMipmaps=!1,Cn.needsUpdate=!0),Cn}class mv{constructor(e={}){const{canvas:t=Rf(),context:n=null,depth:s=!0,stencil:r=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:h="default",failIfMajorPerformanceCaveat:d=!1,reversedDepthBuffer:u=!1,outputBufferType:p=hn}=e;this.isWebGLRenderer=!0;let g;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");g=n.getContextAttributes().alpha}else g=a;const x=p,m=new Set([Ol,Ul,Nl]),f=new Set([hn,On,nr,ir,Dl,Il]),M=new Uint32Array(4),E=new Int32Array(4),y=new P;let T=null,S=null;const R=[],v=[];let w=null;this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=In,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const C=this;let L=!1,N=null,V=null,$=null,F=null;this._outputColorSpace=sn;let W=0,G=0,J=null,te=-1,oe=null;const me=new At,be=new At;let at=null;const gt=new ye(0);let it=0,Y=t.width,ae=t.height,ne=1,Oe=null,Ve=null;const Ie=new At(0,0,Y,ae),Et=new At(0,0,Y,ae);let Je=!1;const j=new Hl;let Ne=!1,ze=!1;const ut=new He,xt=new P,It=new At,$t={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let Rt=!1;function Nt(){return J===null?ne:1}let I=n;function en(b,U){return t.getContext(b,U)}try{const b={alpha:!0,depth:s,stencil:r,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:h,failIfMajorPerformanceCaveat:d};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${Cl}`),t.addEventListener("webglcontextlost",Ct,!1),t.addEventListener("webglcontextrestored",yt,!1),t.addEventListener("webglcontextcreationerror",wn,!1),I===null){const U="webgl2";if(I=en(U,b),I===null)throw en(U)?new Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes."):new Error("THREE.WebGLRenderer: Error creating WebGL context.")}}catch(b){throw st("WebGLRenderer: "+b.message),b}let dt,A,_,O,z,X,re,ce,q,K,he,Pe,fe,ue,Ue,Be,qe,D,le,Z,de,ve,ee;function Ce(){dt=new p_(I),dt.init(),de=new rv(I,dt),A=new a_(I,dt,e,de),_=new iv(I,dt),A.reversedDepthBuffer&&u&&_.buffers.depth.setReversed(!0),V=I.createFramebuffer(),$=I.createFramebuffer(),F=I.createFramebuffer(),O=new __(I),z=new G0,X=new sv(I,dt,_,z,A,de,O),re=new f_(C),ce=new bp(I),ve=new s_(I,ce),q=new m_(I,ce,O,ve),K=new x_(I,q,ce,ve,O),D=new v_(I,A,X),Ue=new o_(z),he=new V0(C,re,dt,A,ve,Ue),Pe=new uv(C,z),fe=new $0,ue=new j0(dt),qe=new i_(C,re,_,K,g,l),Be=new nv(C,K,A),ee=new dv(I,O,A,_),le=new r_(I,dt,O),Z=new g_(I,dt,O),O.programs=he.programs,C.capabilities=A,C.extensions=dt,C.properties=z,C.renderLists=fe,C.shadowMap=Be,C.state=_,C.info=O}Ce(),x!==hn&&(w=new b_(x,t.width,t.height,o,s,r));const Te=new cv(C,I);this.xr=Te,this.getContext=function(){return I},this.getContextAttributes=function(){return I.getContextAttributes()},this.forceContextLoss=function(){const b=dt.get("WEBGL_lose_context");b&&b.loseContext()},this.forceContextRestore=function(){const b=dt.get("WEBGL_lose_context");b&&b.restoreContext()},this.getPixelRatio=function(){return ne},this.setPixelRatio=function(b){b!==void 0&&(ne=b,this.setSize(Y,ae,!1))},this.getSize=function(b){return b.set(Y,ae)},this.setSize=function(b,U,H=!0){if(Te.isPresenting){ke("WebGLRenderer: Can't change size while VR device is presenting.");return}Y=b,ae=U,t.width=Math.floor(b*ne),t.height=Math.floor(U*ne),H===!0&&(t.style.width=b+"px",t.style.height=U+"px"),w!==null&&w.setSize(t.width,t.height),this.setViewport(0,0,b,U)},this.getDrawingBufferSize=function(b){return b.set(Y*ne,ae*ne).floor()},this.setDrawingBufferSize=function(b,U,H){Y=b,ae=U,ne=H,t.width=Math.floor(b*H),t.height=Math.floor(U*H),this.setViewport(0,0,b,U)},this.setEffects=function(b){if(x===hn){st("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(b){for(let U=0;U<b.length;U++)if(b[U].isOutputPass===!0){ke("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}w.setEffects(b||[])},this.getCurrentViewport=function(b){return b.copy(me)},this.getViewport=function(b){return b.copy(Ie)},this.setViewport=function(b,U,H,k){b.isVector4?Ie.set(b.x,b.y,b.z,b.w):Ie.set(b,U,H,k),_.viewport(me.copy(Ie).multiplyScalar(ne).round())},this.getScissor=function(b){return b.copy(Et)},this.setScissor=function(b,U,H,k){b.isVector4?Et.set(b.x,b.y,b.z,b.w):Et.set(b,U,H,k),_.scissor(be.copy(Et).multiplyScalar(ne).round())},this.getScissorTest=function(){return Je},this.setScissorTest=function(b){_.setScissorTest(Je=b)},this.setOpaqueSort=function(b){Oe=b},this.setTransparentSort=function(b){Ve=b},this.getClearColor=function(b){return b.copy(qe.getClearColor())},this.setClearColor=function(){qe.setClearColor(...arguments)},this.getClearAlpha=function(){return qe.getClearAlpha()},this.setClearAlpha=function(){qe.setClearAlpha(...arguments)},this.clear=function(b=!0,U=!0,H=!0){let k=0;if(b){let B=!1;if(J!==null){const _e=J.texture.format;B=m.has(_e)}if(B){const _e=J.texture.type,Se=f.has(_e),ge=qe.getClearColor(),Ae=qe.getClearAlpha(),Le=ge.r,Ye=ge.g,je=ge.b;Se?(M[0]=Le,M[1]=Ye,M[2]=je,M[3]=Ae,I.clearBufferuiv(I.COLOR,0,M)):(E[0]=Le,E[1]=Ye,E[2]=je,E[3]=Ae,I.clearBufferiv(I.COLOR,0,E))}else k|=I.COLOR_BUFFER_BIT}U&&(k|=I.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),H&&(k|=I.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),k!==0&&I.clear(k)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(b){b.setRenderer(this),N=b},this.dispose=function(){t.removeEventListener("webglcontextlost",Ct,!1),t.removeEventListener("webglcontextrestored",yt,!1),t.removeEventListener("webglcontextcreationerror",wn,!1),qe.dispose(),fe.dispose(),ue.dispose(),z.dispose(),re.dispose(),K.dispose(),ve.dispose(),ee.dispose(),he.dispose(),Te.dispose(),Te.removeEventListener("sessionstart",lc),Te.removeEventListener("sessionend",cc),Ti.stop()};function Ct(b){b.preventDefault(),Ec("WebGLRenderer: Context Lost."),L=!0}function yt(){Ec("WebGLRenderer: Context Restored."),L=!1;const b=O.autoReset,U=Be.enabled,H=Be.autoUpdate,k=Be.needsUpdate,B=Be.type;Ce(),O.autoReset=b,Be.enabled=U,Be.autoUpdate=H,Be.needsUpdate=k,Be.type=B}function wn(b){st("WebGLRenderer: A WebGL context could not be created. Reason: ",b.statusMessage)}function Tn(b){const U=b.target;U.removeEventListener("dispose",Tn),Bd(U)}function Bd(b){zd(b),z.remove(b)}function zd(b){const U=z.get(b).programs;U!==void 0&&(U.forEach(function(H){he.releaseProgram(H)}),b.isShaderMaterial&&he.releaseShaderCache(b))}this.renderBufferDirect=function(b,U,H,k,B,_e){U===null&&(U=$t);const Se=B.isMesh&&B.matrixWorld.determinantAffine()<0,ge=Gd(b,U,H,k,B);_.setMaterial(k,Se);let Ae=H.index,Le=1;if(k.wireframe===!0){if(Ae=q.getWireframeAttribute(H),Ae===void 0)return;Le=2}const Ye=H.drawRange,je=H.attributes.position;let De=Ye.start*Le,pt=(Ye.start+Ye.count)*Le;_e!==null&&(De=Math.max(De,_e.start*Le),pt=Math.min(pt,(_e.start+_e.count)*Le)),Ae!==null?(De=Math.max(De,0),pt=Math.min(pt,Ae.count)):je!=null&&(De=Math.max(De,0),pt=Math.min(pt,je.count));const Lt=pt-De;if(Lt<0||Lt===1/0)return;ve.setup(B,k,ge,H,Ae);let Pt,_t=le;if(Ae!==null&&(Pt=ce.get(Ae),_t=Z,_t.setIndex(Pt)),B.isMesh)k.wireframe===!0?(_.setLineWidth(k.wireframeLinewidth*Nt()),_t.setMode(I.LINES)):_t.setMode(I.TRIANGLES);else if(B.isLine){let Xt=k.linewidth;Xt===void 0&&(Xt=1),_.setLineWidth(Xt*Nt()),B.isLineSegments?_t.setMode(I.LINES):B.isLineLoop?_t.setMode(I.LINE_LOOP):_t.setMode(I.LINE_STRIP)}else B.isPoints?_t.setMode(I.POINTS):B.isSprite&&_t.setMode(I.TRIANGLES);if(B.isBatchedMesh)if(dt.get("WEBGL_multi_draw"))_t.renderMultiDraw(B._multiDrawStarts,B._multiDrawCounts,B._multiDrawCount);else{const Xt=B._multiDrawStarts,Me=B._multiDrawCounts,an=B._multiDrawCount,ot=Ae?ce.get(Ae).bytesPerElement:1,dn=z.get(k).currentProgram.getUniforms();for(let An=0;An<an;An++)dn.setValue(I,"_gl_DrawID",An),_t.render(Xt[An]/ot,Me[An])}else if(B.isInstancedMesh)_t.renderInstances(De,Lt,B.count);else if(H.isInstancedBufferGeometry){const Xt=H._maxInstanceCount!==void 0?H._maxInstanceCount:1/0,Me=Math.min(H.instanceCount,Xt);_t.renderInstances(De,Lt,Me)}else _t.render(De,Lt)};function oc(b,U,H){b.transparent===!0&&b.side===pn&&b.forceSinglePass===!1?(b.side=rn,b.needsUpdate=!0,pr(b,U,H),b.side=vi,b.needsUpdate=!0,pr(b,U,H),b.side=pn):pr(b,U,H)}this.compile=function(b,U,H=null){H===null&&(H=b),S=ue.get(H),S.init(U),v.push(S),H.traverseVisible(function(B){B.isLight&&B.layers.test(U.layers)&&(S.pushLight(B),B.castShadow&&S.pushShadow(B))}),b!==H&&b.traverseVisible(function(B){B.isLight&&B.layers.test(U.layers)&&(S.pushLight(B),B.castShadow&&S.pushShadow(B))}),S.setupLights();const k=new Set;return b.traverse(function(B){if(!(B.isMesh||B.isPoints||B.isLine||B.isSprite))return;const _e=B.material;if(_e)if(Array.isArray(_e))for(let Se=0;Se<_e.length;Se++){const ge=_e[Se];oc(ge,H,B),k.add(ge)}else oc(_e,H,B),k.add(_e)}),S=v.pop(),k},this.compileAsync=function(b,U,H=null){const k=this.compile(b,U,H);return new Promise(B=>{function _e(){if(k.forEach(function(Se){z.get(Se).currentProgram.isReady()&&k.delete(Se)}),k.size===0){B(b);return}setTimeout(_e,10)}dt.get("KHR_parallel_shader_compile")!==null?_e():setTimeout(_e,10)})};let Aa=null;function Hd(b){Aa&&Aa(b)}function lc(){Ti.stop()}function cc(){Ti.start()}const Ti=new id;Ti.setAnimationLoop(Hd),typeof self<"u"&&Ti.setContext(self),this.setAnimationLoop=function(b){Aa=b,Te.setAnimationLoop(b),b===null?Ti.stop():Ti.start()},Te.addEventListener("sessionstart",lc),Te.addEventListener("sessionend",cc),this.render=function(b,U){if(U!==void 0&&U.isCamera!==!0){st("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(L===!0)return;N!==null&&N.renderStart(b,U);const H=Te.enabled===!0&&Te.isPresenting===!0,k=w!==null&&(J===null||H)&&w.begin(C,J);if(b.matrixWorldAutoUpdate===!0&&b.updateMatrixWorld(),U.parent===null&&U.matrixWorldAutoUpdate===!0&&U.updateMatrixWorld(),Te.enabled===!0&&Te.isPresenting===!0&&(w===null||w.isCompositing()===!1)&&(Te.cameraAutoUpdate===!0&&Te.updateCamera(U),U=Te.getCamera()),b.isScene===!0&&b.onBeforeRender(C,b,U,J),S=ue.get(b,v.length),S.init(U),S.state.textureUnits=X.getTextureUnits(),v.push(S),ut.multiplyMatrices(U.projectionMatrix,U.matrixWorldInverse),j.setFromProjectionMatrix(ut,Dn,U.reversedDepth),ze=this.localClippingEnabled,Ne=Ue.init(this.clippingPlanes,ze),T=fe.get(b,R.length),T.init(),R.push(T),Te.enabled===!0&&Te.isPresenting===!0){const Se=C.xr.getDepthSensingMesh();Se!==null&&Ra(Se,U,-1/0,C.sortObjects)}Ra(b,U,0,C.sortObjects),T.finish(),C.sortObjects===!0&&T.sort(Oe,Ve,U.reversedDepth),Rt=Te.enabled===!1||Te.isPresenting===!1||Te.hasDepthSensing()===!1,Rt&&qe.addToRenderList(T,b),this.info.render.frame++,this.info.autoReset===!0&&this.info.reset(),Ne===!0&&Ue.beginShadows();const B=S.state.shadowsArray;if(Be.render(B,b,U),Ne===!0&&Ue.endShadows(),(k&&w.hasRenderPass())===!1){const Se=T.opaque,ge=T.transmissive;if(S.setupLights(),U.isArrayCamera){const Ae=U.cameras;if(ge.length>0)for(let Le=0,Ye=Ae.length;Le<Ye;Le++){const je=Ae[Le];uc(Se,ge,b,je)}Rt&&qe.render(b);for(let Le=0,Ye=Ae.length;Le<Ye;Le++){const je=Ae[Le];hc(T,b,je,je.viewport)}}else ge.length>0&&uc(Se,ge,b,U),Rt&&qe.render(b),hc(T,b,U)}J!==null&&G===0&&(X.updateMultisampleRenderTarget(J),X.updateRenderTargetMipmap(J)),k&&w.end(C),b.isScene===!0&&b.onAfterRender(C,b,U),ve.resetDefaultState(),te=-1,oe=null,v.pop(),v.length>0?(S=v[v.length-1],X.setTextureUnits(S.state.textureUnits),Ne===!0&&Ue.setGlobalState(C.clippingPlanes,S.state.camera)):S=null,R.pop(),R.length>0?T=R[R.length-1]:T=null,N!==null&&N.renderEnd()};function Ra(b,U,H,k){if(b.visible===!1)return;if(b.layers.test(U.layers)){if(b.isGroup)H=b.renderOrder;else if(b.isLOD)b.autoUpdate===!0&&b.update(U);else if(b.isLightProbeGrid)S.pushLightProbeGrid(b);else if(b.isLight)S.pushLight(b),b.castShadow&&S.pushShadow(b);else if(b.isSprite){if(!b.frustumCulled||j.intersectsSprite(b)){k&&It.setFromMatrixPosition(b.matrixWorld).applyMatrix4(ut);const Se=K.update(b),ge=b.material;ge.visible&&T.push(b,Se,ge,H,It.z,null)}}else if((b.isMesh||b.isLine||b.isPoints)&&(!b.frustumCulled||j.intersectsObject(b))){const Se=K.update(b),ge=b.material;if(k&&(b.boundingSphere!==void 0?(b.boundingSphere===null&&b.computeBoundingSphere(),It.copy(b.boundingSphere.center)):(Se.boundingSphere===null&&Se.computeBoundingSphere(),It.copy(Se.boundingSphere.center)),It.applyMatrix4(b.matrixWorld).applyMatrix4(ut)),Array.isArray(ge)){const Ae=Se.groups;for(let Le=0,Ye=Ae.length;Le<Ye;Le++){const je=Ae[Le],De=ge[je.materialIndex];De&&De.visible&&T.push(b,Se,De,H,It.z,je)}}else ge.visible&&T.push(b,Se,ge,H,It.z,null)}}const _e=b.children;for(let Se=0,ge=_e.length;Se<ge;Se++)Ra(_e[Se],U,H,k)}function hc(b,U,H,k){const{opaque:B,transmissive:_e,transparent:Se}=b;S.setupLightsView(H),Ne===!0&&Ue.setGlobalState(C.clippingPlanes,H),k&&_.viewport(me.copy(k)),B.length>0&&fr(B,U,H),_e.length>0&&fr(_e,U,H),Se.length>0&&fr(Se,U,H),_.buffers.depth.setTest(!0),_.buffers.depth.setMask(!0),_.buffers.color.setMask(!0),_.setPolygonOffset(!1)}function uc(b,U,H,k){if((H.isScene===!0?H.overrideMaterial:null)!==null)return;if(S.state.transmissionRenderTarget[k.id]===void 0){const De=dt.has("EXT_color_buffer_half_float")||dt.has("EXT_color_buffer_float");S.state.transmissionRenderTarget[k.id]=new Nn(1,1,{generateMipmaps:!0,type:De?Kn:hn,minFilter:$n,samples:Math.max(4,A.samples),stencilBuffer:r,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:et.workingColorSpace})}const _e=S.state.transmissionRenderTarget[k.id],Se=k.viewport||me;_e.setSize(Se.z*C.transmissionResolutionScale,Se.w*C.transmissionResolutionScale);const ge=C.getRenderTarget(),Ae=C.getActiveCubeFace(),Le=C.getActiveMipmapLevel();C.setRenderTarget(_e),C.getClearColor(gt),it=C.getClearAlpha(),it<1&&C.setClearColor(16777215,.5),C.clear(),Rt&&qe.render(H);const Ye=C.toneMapping;C.toneMapping=In;const je=k.viewport;if(k.viewport!==void 0&&(k.viewport=void 0),S.setupLightsView(k),Ne===!0&&Ue.setGlobalState(C.clippingPlanes,k),fr(b,H,k),X.updateMultisampleRenderTarget(_e),X.updateRenderTargetMipmap(_e),dt.has("WEBGL_multisampled_render_to_texture")===!1){let De=!1;for(let pt=0,Lt=U.length;pt<Lt;pt++){const Pt=U[pt],{object:_t,geometry:Xt,material:Me,group:an}=Pt;if(Me.side===pn&&_t.layers.test(k.layers)){const ot=Me.side;Me.side=rn,Me.needsUpdate=!0,dc(_t,H,k,Xt,Me,an),Me.side=ot,Me.needsUpdate=!0,De=!0}}De===!0&&(X.updateMultisampleRenderTarget(_e),X.updateRenderTargetMipmap(_e))}C.setRenderTarget(ge,Ae,Le),C.setClearColor(gt,it),je!==void 0&&(k.viewport=je),C.toneMapping=Ye}function fr(b,U,H){const k=U.isScene===!0?U.overrideMaterial:null;for(let B=0,_e=b.length;B<_e;B++){const Se=b[B],{object:ge,geometry:Ae,group:Le}=Se;let Ye=Se.material;Ye.allowOverride===!0&&k!==null&&(Ye=k),ge.layers.test(H.layers)&&dc(ge,U,H,Ae,Ye,Le)}}function dc(b,U,H,k,B,_e){b.onBeforeRender(C,U,H,k,B,_e),b.modelViewMatrix.multiplyMatrices(H.matrixWorldInverse,b.matrixWorld),b.normalMatrix.getNormalMatrix(b.modelViewMatrix),B.onBeforeRender(C,U,H,k,b,_e),B.transparent===!0&&B.side===pn&&B.forceSinglePass===!1?(B.side=rn,B.needsUpdate=!0,C.renderBufferDirect(H,U,k,B,b,_e),B.side=vi,B.needsUpdate=!0,C.renderBufferDirect(H,U,k,B,b,_e),B.side=pn):C.renderBufferDirect(H,U,k,B,b,_e),b.onAfterRender(C,U,H,k,B,_e)}function pr(b,U,H){U.isScene!==!0&&(U=$t);const k=z.get(b),B=S.state.lights,_e=S.state.shadowsArray,Se=B.state.version,ge=he.getParameters(b,B.state,_e,U,H,S.state.lightProbeGridArray),Ae=he.getProgramCacheKey(ge);let Le=k.programs;k.environment=b.isMeshStandardMaterial||b.isMeshLambertMaterial||b.isMeshPhongMaterial?U.environment:null,k.fog=U.fog;const Ye=b.isMeshStandardMaterial||b.isMeshLambertMaterial&&!b.envMap||b.isMeshPhongMaterial&&!b.envMap;k.envMap=re.get(b.envMap||k.environment,Ye),k.envMapRotation=k.environment!==null&&b.envMap===null?U.environmentRotation:b.envMapRotation,Le===void 0&&(b.addEventListener("dispose",Tn),Le=new Map,k.programs=Le);let je=Le.get(Ae);if(je!==void 0){if(k.currentProgram===je&&k.lightsStateVersion===Se)return pc(b,ge),je}else ge.uniforms=he.getUniforms(b),N!==null&&b.isNodeMaterial&&N.build(b,H,ge),b.onBeforeCompile(ge,C),je=he.acquireProgram(ge,Ae),Le.set(Ae,je),k.uniforms=ge.uniforms;const De=k.uniforms;return(!b.isShaderMaterial&&!b.isRawShaderMaterial||b.clipping===!0)&&(De.clippingPlanes=Ue.uniform),pc(b,ge),k.needsLights=$d(b),k.lightsStateVersion=Se,k.needsLights&&(De.ambientLightColor.value=B.state.ambient,De.lightProbe.value=B.state.probe,De.directionalLights.value=B.state.directional,De.directionalLightShadows.value=B.state.directionalShadow,De.spotLights.value=B.state.spot,De.spotLightShadows.value=B.state.spotShadow,De.rectAreaLights.value=B.state.rectArea,De.ltc_1.value=B.state.rectAreaLTC1,De.ltc_2.value=B.state.rectAreaLTC2,De.pointLights.value=B.state.point,De.pointLightShadows.value=B.state.pointShadow,De.hemisphereLights.value=B.state.hemi,De.directionalShadowMatrix.value=B.state.directionalShadowMatrix,De.spotLightMatrix.value=B.state.spotLightMatrix,De.spotLightMap.value=B.state.spotLightMap,De.pointShadowMatrix.value=B.state.pointShadowMatrix),k.lightProbeGrid=S.state.lightProbeGridArray.length>0,k.currentProgram=je,k.uniformsList=null,je}function fc(b){if(b.uniformsList===null){const U=b.currentProgram.getUniforms();b.uniformsList=ia.seqWithValue(U.seq,b.uniforms)}return b.uniformsList}function pc(b,U){const H=z.get(b);H.outputColorSpace=U.outputColorSpace,H.batching=U.batching,H.batchingColor=U.batchingColor,H.instancing=U.instancing,H.instancingColor=U.instancingColor,H.instancingMorph=U.instancingMorph,H.skinning=U.skinning,H.morphTargets=U.morphTargets,H.morphNormals=U.morphNormals,H.morphColors=U.morphColors,H.morphTargetsCount=U.morphTargetsCount,H.numClippingPlanes=U.numClippingPlanes,H.numIntersection=U.numClipIntersection,H.vertexAlphas=U.vertexAlphas,H.vertexTangents=U.vertexTangents,H.toneMapping=U.toneMapping}function Vd(b,U){if(b.length===0)return null;if(b.length===1)return b[0].texture!==null?b[0]:null;y.setFromMatrixPosition(U.matrixWorld);for(let H=0,k=b.length;H<k;H++){const B=b[H];if(B.texture!==null&&B.boundingBox.containsPoint(y))return B}return null}function Gd(b,U,H,k,B){U.isScene!==!0&&(U=$t),X.resetTextureUnits();const _e=U.fog,Se=k.isMeshStandardMaterial||k.isMeshLambertMaterial||k.isMeshPhongMaterial?U.environment:null,ge=J===null?C.outputColorSpace:J.isXRRenderTarget===!0?J.texture.colorSpace:et.workingColorSpace,Ae=k.isMeshStandardMaterial||k.isMeshLambertMaterial&&!k.envMap||k.isMeshPhongMaterial&&!k.envMap,Le=re.get(k.envMap||Se,Ae),Ye=k.vertexColors===!0&&!!H.attributes.color&&H.attributes.color.itemSize===4,je=!!H.attributes.tangent&&(!!k.normalMap||k.anisotropy>0),De=!!H.morphAttributes.position,pt=!!H.morphAttributes.normal,Lt=!!H.morphAttributes.color;let Pt=In;k.toneMapped&&(J===null||J.isXRRenderTarget===!0)&&(Pt=C.toneMapping);const _t=H.morphAttributes.position||H.morphAttributes.normal||H.morphAttributes.color,Xt=_t!==void 0?_t.length:0,Me=z.get(k),an=S.state.lights;if(Ne===!0&&(ze===!0||b!==oe)){const bt=b===oe&&k.id===te;Ue.setState(k,b,bt)}let ot=!1;k.version===Me.__version?(Me.needsLights&&Me.lightsStateVersion!==an.state.version||Me.outputColorSpace!==ge||B.isBatchedMesh&&Me.batching===!1||!B.isBatchedMesh&&Me.batching===!0||B.isBatchedMesh&&Me.batchingColor===!0&&B.colorTexture===null||B.isBatchedMesh&&Me.batchingColor===!1&&B.colorTexture!==null||B.isInstancedMesh&&Me.instancing===!1||!B.isInstancedMesh&&Me.instancing===!0||B.isSkinnedMesh&&Me.skinning===!1||!B.isSkinnedMesh&&Me.skinning===!0||B.isInstancedMesh&&Me.instancingColor===!0&&B.instanceColor===null||B.isInstancedMesh&&Me.instancingColor===!1&&B.instanceColor!==null||B.isInstancedMesh&&Me.instancingMorph===!0&&B.morphTexture===null||B.isInstancedMesh&&Me.instancingMorph===!1&&B.morphTexture!==null||Me.envMap!==Le||k.fog===!0&&Me.fog!==_e||Me.numClippingPlanes!==void 0&&(Me.numClippingPlanes!==Ue.numPlanes||Me.numIntersection!==Ue.numIntersection)||Me.vertexAlphas!==Ye||Me.vertexTangents!==je||Me.morphTargets!==De||Me.morphNormals!==pt||Me.morphColors!==Lt||Me.toneMapping!==Pt||Me.morphTargetsCount!==Xt||!!Me.lightProbeGrid!=S.state.lightProbeGridArray.length>0)&&(ot=!0):(ot=!0,Me.__version=k.version);let dn=Me.currentProgram;ot===!0&&(dn=pr(k,U,B),N&&k.isNodeMaterial&&N.onUpdateProgram(k,dn,Me));let An=!1,ei=!1,Vi=!1;const vt=dn.getUniforms(),Dt=Me.uniforms;if(_.useProgram(dn.program)&&(An=!0,ei=!0,Vi=!0),k.id!==te&&(te=k.id,ei=!0),Me.needsLights){const bt=Vd(S.state.lightProbeGridArray,B);Me.lightProbeGrid!==bt&&(Me.lightProbeGrid=bt,ei=!0)}if(An||oe!==b){_.buffers.depth.getReversed()&&b.reversedDepth!==!0&&(b._reversedDepth=!0,b.updateProjectionMatrix()),vt.setValue(I,"projectionMatrix",b.projectionMatrix),vt.setValue(I,"viewMatrix",b.matrixWorldInverse);const ni=vt.map.cameraPosition;ni!==void 0&&ni.setValue(I,xt.setFromMatrixPosition(b.matrixWorld)),A.logarithmicDepthBuffer&&vt.setValue(I,"logDepthBufFC",2/(Math.log(b.far+1)/Math.LN2)),(k.isMeshPhongMaterial||k.isMeshToonMaterial||k.isMeshLambertMaterial||k.isMeshBasicMaterial||k.isMeshStandardMaterial||k.isShaderMaterial)&&vt.setValue(I,"isOrthographic",b.isOrthographicCamera===!0),oe!==b&&(oe=b,ei=!0,Vi=!0)}if(Me.needsLights&&(an.state.directionalShadowMap.length>0&&vt.setValue(I,"directionalShadowMap",an.state.directionalShadowMap,X),an.state.spotShadowMap.length>0&&vt.setValue(I,"spotShadowMap",an.state.spotShadowMap,X),an.state.pointShadowMap.length>0&&vt.setValue(I,"pointShadowMap",an.state.pointShadowMap,X)),B.isSkinnedMesh){vt.setOptional(I,B,"bindMatrix"),vt.setOptional(I,B,"bindMatrixInverse");const bt=B.skeleton;bt&&(bt.boneTexture===null&&bt.computeBoneTexture(),vt.setValue(I,"boneTexture",bt.boneTexture,X))}B.isBatchedMesh&&(vt.setOptional(I,B,"batchingTexture"),vt.setValue(I,"batchingTexture",B._matricesTexture,X),vt.setOptional(I,B,"batchingIdTexture"),vt.setValue(I,"batchingIdTexture",B._indirectTexture,X),vt.setOptional(I,B,"batchingColorTexture"),B._colorsTexture!==null&&vt.setValue(I,"batchingColorTexture",B._colorsTexture,X));const ti=H.morphAttributes;if((ti.position!==void 0||ti.normal!==void 0||ti.color!==void 0)&&D.update(B,H,dn),(ei||Me.receiveShadow!==B.receiveShadow)&&(Me.receiveShadow=B.receiveShadow,vt.setValue(I,"receiveShadow",B.receiveShadow)),(k.isMeshStandardMaterial||k.isMeshLambertMaterial||k.isMeshPhongMaterial)&&k.envMap===null&&U.environment!==null&&(Dt.envMapIntensity.value=U.environmentIntensity),Dt.dfgLUT!==void 0&&(Dt.dfgLUT.value=pv()),ei){if(vt.setValue(I,"toneMappingExposure",C.toneMappingExposure),Me.needsLights&&Wd(Dt,Vi),_e&&k.fog===!0&&Pe.refreshFogUniforms(Dt,_e),Pe.refreshMaterialUniforms(Dt,k,ne,ae,S.state.transmissionRenderTarget[b.id]),Me.needsLights&&Me.lightProbeGrid){const bt=Me.lightProbeGrid;Dt.probesSH.value=bt.texture,Dt.probesMin.value.copy(bt.boundingBox.min),Dt.probesMax.value.copy(bt.boundingBox.max),Dt.probesResolution.value.copy(bt.resolution)}ia.upload(I,fc(Me),Dt,X)}if(k.isShaderMaterial&&k.uniformsNeedUpdate===!0&&(ia.upload(I,fc(Me),Dt,X),k.uniformsNeedUpdate=!1),k.isSpriteMaterial&&vt.setValue(I,"center",B.center),vt.setValue(I,"modelViewMatrix",B.modelViewMatrix),vt.setValue(I,"normalMatrix",B.normalMatrix),vt.setValue(I,"modelMatrix",B.matrixWorld),k.uniformsGroups!==void 0){const bt=k.uniformsGroups;for(let ni=0,Gi=bt.length;ni<Gi;ni++){const mc=bt[ni];ee.update(mc,dn),ee.bind(mc,dn)}}return dn}function Wd(b,U){b.ambientLightColor.needsUpdate=U,b.lightProbe.needsUpdate=U,b.directionalLights.needsUpdate=U,b.directionalLightShadows.needsUpdate=U,b.pointLights.needsUpdate=U,b.pointLightShadows.needsUpdate=U,b.spotLights.needsUpdate=U,b.spotLightShadows.needsUpdate=U,b.rectAreaLights.needsUpdate=U,b.hemisphereLights.needsUpdate=U}function $d(b){return b.isMeshLambertMaterial||b.isMeshToonMaterial||b.isMeshPhongMaterial||b.isMeshStandardMaterial||b.isShadowMaterial||b.isShaderMaterial&&b.lights===!0}this.getActiveCubeFace=function(){return W},this.getActiveMipmapLevel=function(){return G},this.getRenderTarget=function(){return J},this.setRenderTargetTextures=function(b,U,H){const k=z.get(b);k.__autoAllocateDepthBuffer=b.resolveDepthBuffer===!1,k.__autoAllocateDepthBuffer===!1&&(k.__useRenderToTexture=!1),z.get(b.texture).__webglTexture=U,z.get(b.depthTexture).__webglTexture=k.__autoAllocateDepthBuffer?void 0:H,k.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(b,U){const H=z.get(b);H.__webglFramebuffer=U,H.__useDefaultFramebuffer=U===void 0},this.setRenderTarget=function(b,U=0,H=0){J=b,W=U,G=H;let k=null,B=!1,_e=!1;if(b){const ge=z.get(b);if(ge.__useDefaultFramebuffer!==void 0){_.bindFramebuffer(I.FRAMEBUFFER,ge.__webglFramebuffer),me.copy(b.viewport),be.copy(b.scissor),at=b.scissorTest,_.viewport(me),_.scissor(be),_.setScissorTest(at),te=-1;return}else if(ge.__webglFramebuffer===void 0)X.setupRenderTarget(b);else if(ge.__hasExternalTextures)X.rebindTextures(b,z.get(b.texture).__webglTexture,z.get(b.depthTexture).__webglTexture);else if(b.depthBuffer){const Ye=b.depthTexture;if(ge.__boundDepthTexture!==Ye){if(Ye!==null&&z.has(Ye)&&(b.width!==Ye.image.width||b.height!==Ye.image.height))throw new Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");X.setupDepthRenderbuffer(b)}}const Ae=b.texture;(Ae.isData3DTexture||Ae.isDataArrayTexture||Ae.isCompressedArrayTexture)&&(_e=!0);const Le=z.get(b).__webglFramebuffer;b.isWebGLCubeRenderTarget?(Array.isArray(Le[U])?k=Le[U][H]:k=Le[U],B=!0):b.samples>0&&X.useMultisampledRTT(b)===!1?k=z.get(b).__webglMultisampledFramebuffer:Array.isArray(Le)?k=Le[H]:k=Le,me.copy(b.viewport),be.copy(b.scissor),at=b.scissorTest}else me.copy(Ie).multiplyScalar(ne).floor(),be.copy(Et).multiplyScalar(ne).floor(),at=Je;if(H!==0&&(k=V),_.bindFramebuffer(I.FRAMEBUFFER,k)&&_.drawBuffers(b,k),_.viewport(me),_.scissor(be),_.setScissorTest(at),B){const ge=z.get(b.texture);I.framebufferTexture2D(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_CUBE_MAP_POSITIVE_X+U,ge.__webglTexture,H)}else if(_e){const ge=U;for(let Ae=0;Ae<b.textures.length;Ae++){const Le=z.get(b.textures[Ae]);I.framebufferTextureLayer(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0+Ae,Le.__webglTexture,H,ge)}}else if(b!==null&&H!==0){const ge=z.get(b.texture);I.framebufferTexture2D(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,ge.__webglTexture,H)}te=-1},this.readRenderTargetPixels=function(b,U,H,k,B,_e,Se,ge=0){if(!(b&&b.isWebGLRenderTarget)){st("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let Ae=z.get(b).__webglFramebuffer;if(b.isWebGLCubeRenderTarget&&Se!==void 0&&(Ae=Ae[Se]),Ae){_.bindFramebuffer(I.FRAMEBUFFER,Ae);try{const Le=b.textures[ge],Ye=Le.format,je=Le.type;if(b.textures.length>1&&I.readBuffer(I.COLOR_ATTACHMENT0+ge),!A.textureFormatReadable(Ye)){st("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!A.textureTypeReadable(je)){st("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}U>=0&&U<=b.width-k&&H>=0&&H<=b.height-B&&I.readPixels(U,H,k,B,de.convert(Ye),de.convert(je),_e)}finally{const Le=J!==null?z.get(J).__webglFramebuffer:null;_.bindFramebuffer(I.FRAMEBUFFER,Le)}}},this.readRenderTargetPixelsAsync=async function(b,U,H,k,B,_e,Se,ge=0){if(!(b&&b.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let Ae=z.get(b).__webglFramebuffer;if(b.isWebGLCubeRenderTarget&&Se!==void 0&&(Ae=Ae[Se]),Ae)if(U>=0&&U<=b.width-k&&H>=0&&H<=b.height-B){_.bindFramebuffer(I.FRAMEBUFFER,Ae);const Le=b.textures[ge],Ye=Le.format,je=Le.type;if(b.textures.length>1&&I.readBuffer(I.COLOR_ATTACHMENT0+ge),!A.textureFormatReadable(Ye))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!A.textureTypeReadable(je))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const De=I.createBuffer();I.bindBuffer(I.PIXEL_PACK_BUFFER,De),I.bufferData(I.PIXEL_PACK_BUFFER,_e.byteLength,I.STREAM_READ),I.readPixels(U,H,k,B,de.convert(Ye),de.convert(je),0);const pt=J!==null?z.get(J).__webglFramebuffer:null;_.bindFramebuffer(I.FRAMEBUFFER,pt);const Lt=I.fenceSync(I.SYNC_GPU_COMMANDS_COMPLETE,0);return I.flush(),await Cf(I,Lt,4),I.bindBuffer(I.PIXEL_PACK_BUFFER,De),I.getBufferSubData(I.PIXEL_PACK_BUFFER,0,_e),I.deleteBuffer(De),I.deleteSync(Lt),_e}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(b,U=null,H=0){const k=Math.pow(2,-H),B=Math.floor(b.image.width*k),_e=Math.floor(b.image.height*k),Se=U!==null?U.x:0,ge=U!==null?U.y:0;X.setTexture2D(b,0),I.copyTexSubImage2D(I.TEXTURE_2D,H,0,0,Se,ge,B,_e),_.unbindTexture()},this.copyTextureToTexture=function(b,U,H=null,k=null,B=0,_e=0){let Se,ge,Ae,Le,Ye,je,De,pt,Lt;const Pt=b.isCompressedTexture?b.mipmaps[_e]:b.image;if(H!==null)Se=H.max.x-H.min.x,ge=H.max.y-H.min.y,Ae=H.isBox3?H.max.z-H.min.z:1,Le=H.min.x,Ye=H.min.y,je=H.isBox3?H.min.z:0;else{const Dt=Math.pow(2,-B);Se=Math.floor(Pt.width*Dt),ge=Math.floor(Pt.height*Dt),b.isDataArrayTexture?Ae=Pt.depth:b.isData3DTexture?Ae=Math.floor(Pt.depth*Dt):Ae=1,Le=0,Ye=0,je=0}k!==null?(De=k.x,pt=k.y,Lt=k.z):(De=0,pt=0,Lt=0);const _t=de.convert(U.format),Xt=de.convert(U.type);let Me;U.isData3DTexture?(X.setTexture3D(U,0),Me=I.TEXTURE_3D):U.isDataArrayTexture||U.isCompressedArrayTexture?(X.setTexture2DArray(U,0),Me=I.TEXTURE_2D_ARRAY):(X.setTexture2D(U,0),Me=I.TEXTURE_2D),_.activeTexture(I.TEXTURE0),_.pixelStorei(I.UNPACK_FLIP_Y_WEBGL,U.flipY),_.pixelStorei(I.UNPACK_PREMULTIPLY_ALPHA_WEBGL,U.premultiplyAlpha),_.pixelStorei(I.UNPACK_ALIGNMENT,U.unpackAlignment);const an=_.getParameter(I.UNPACK_ROW_LENGTH),ot=_.getParameter(I.UNPACK_IMAGE_HEIGHT),dn=_.getParameter(I.UNPACK_SKIP_PIXELS),An=_.getParameter(I.UNPACK_SKIP_ROWS),ei=_.getParameter(I.UNPACK_SKIP_IMAGES);_.pixelStorei(I.UNPACK_ROW_LENGTH,Pt.width),_.pixelStorei(I.UNPACK_IMAGE_HEIGHT,Pt.height),_.pixelStorei(I.UNPACK_SKIP_PIXELS,Le),_.pixelStorei(I.UNPACK_SKIP_ROWS,Ye),_.pixelStorei(I.UNPACK_SKIP_IMAGES,je);const Vi=b.isDataArrayTexture||b.isData3DTexture,vt=U.isDataArrayTexture||U.isData3DTexture;if(b.isDepthTexture){const Dt=z.get(b),ti=z.get(U),bt=z.get(Dt.__renderTarget),ni=z.get(ti.__renderTarget);_.bindFramebuffer(I.READ_FRAMEBUFFER,bt.__webglFramebuffer),_.bindFramebuffer(I.DRAW_FRAMEBUFFER,ni.__webglFramebuffer);for(let Gi=0;Gi<Ae;Gi++)Vi&&(I.framebufferTextureLayer(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,z.get(b).__webglTexture,B,je+Gi),I.framebufferTextureLayer(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,z.get(U).__webglTexture,_e,Lt+Gi)),I.blitFramebuffer(Le,Ye,Se,ge,De,pt,Se,ge,I.DEPTH_BUFFER_BIT,I.NEAREST);_.bindFramebuffer(I.READ_FRAMEBUFFER,null),_.bindFramebuffer(I.DRAW_FRAMEBUFFER,null)}else if(B!==0||b.isRenderTargetTexture||z.has(b)){const Dt=z.get(b),ti=z.get(U);_.bindFramebuffer(I.READ_FRAMEBUFFER,$),_.bindFramebuffer(I.DRAW_FRAMEBUFFER,F);for(let bt=0;bt<Ae;bt++)Vi?I.framebufferTextureLayer(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,Dt.__webglTexture,B,je+bt):I.framebufferTexture2D(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,Dt.__webglTexture,B),vt?I.framebufferTextureLayer(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,ti.__webglTexture,_e,Lt+bt):I.framebufferTexture2D(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,ti.__webglTexture,_e),B!==0?I.blitFramebuffer(Le,Ye,Se,ge,De,pt,Se,ge,I.COLOR_BUFFER_BIT,I.NEAREST):vt?I.copyTexSubImage3D(Me,_e,De,pt,Lt+bt,Le,Ye,Se,ge):I.copyTexSubImage2D(Me,_e,De,pt,Le,Ye,Se,ge);_.bindFramebuffer(I.READ_FRAMEBUFFER,null),_.bindFramebuffer(I.DRAW_FRAMEBUFFER,null)}else vt?b.isDataTexture||b.isData3DTexture?I.texSubImage3D(Me,_e,De,pt,Lt,Se,ge,Ae,_t,Xt,Pt.data):U.isCompressedArrayTexture?I.compressedTexSubImage3D(Me,_e,De,pt,Lt,Se,ge,Ae,_t,Pt.data):I.texSubImage3D(Me,_e,De,pt,Lt,Se,ge,Ae,_t,Xt,Pt):b.isDataTexture?I.texSubImage2D(I.TEXTURE_2D,_e,De,pt,Se,ge,_t,Xt,Pt.data):b.isCompressedTexture?I.compressedTexSubImage2D(I.TEXTURE_2D,_e,De,pt,Pt.width,Pt.height,_t,Pt.data):I.texSubImage2D(I.TEXTURE_2D,_e,De,pt,Se,ge,_t,Xt,Pt);_.pixelStorei(I.UNPACK_ROW_LENGTH,an),_.pixelStorei(I.UNPACK_IMAGE_HEIGHT,ot),_.pixelStorei(I.UNPACK_SKIP_PIXELS,dn),_.pixelStorei(I.UNPACK_SKIP_ROWS,An),_.pixelStorei(I.UNPACK_SKIP_IMAGES,ei),_e===0&&U.generateMipmaps&&I.generateMipmap(Me),_.unbindTexture()},this.initRenderTarget=function(b){z.get(b).__webglFramebuffer===void 0&&X.setupRenderTarget(b)},this.initTexture=function(b){b.isCubeTexture?X.setTextureCube(b,0):b.isData3DTexture?X.setTexture3D(b,0):b.isDataArrayTexture||b.isCompressedArrayTexture?X.setTexture2DArray(b,0):X.setTexture2D(b,0),_.unbindTexture()},this.resetState=function(){W=0,G=0,J=null,_.reset(),ve.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Dn}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const t=this.getContext();t.drawingBufferColorSpace=et._getDrawingBufferColorSpace(e),t.unpackColorSpace=et._getUnpackColorSpace()}}class Yl extends Bt{constructor(e=document.createElement("div")){super(),this.isCSS2DObject=!0,this.element=e,this.element.style.position="absolute",this.element.style.userSelect="none",this.element.setAttribute("draggable",!1),this.center=new Fe(.5,.5),this.addEventListener("removed",function(){this.traverse(function(t){t.element&&t.element instanceof t.element.ownerDocument.defaultView.Element&&t.element.parentNode!==null&&t.element.remove()})})}copy(e,t){return super.copy(e,t),this.element=e.element.cloneNode(!0),this.center=e.center,this}}const rs=new P,wh=new He,Th=new He,Ah=new P,Rh=new P;class gv{constructor(e={}){const t=this;let n,s,r,a;const o={objects:new WeakMap},l=e.element!==void 0?e.element:document.createElement("div");l.style.overflow="hidden",this.domElement=l,this.sortObjects=!0,this.getSize=function(){return{width:n,height:s}},this.render=function(g,x){g.matrixWorldAutoUpdate===!0&&g.updateMatrixWorld(),x.parent===null&&x.matrixWorldAutoUpdate===!0&&x.updateMatrixWorld(),wh.copy(x.matrixWorldInverse),Th.multiplyMatrices(x.projectionMatrix,wh),h(g,g,x),this.sortObjects&&p(g)},this.setSize=function(g,x){n=g,s=x,r=n/2,a=s/2,l.style.width=g+"px",l.style.height=x+"px"};function c(g){g.isCSS2DObject&&(g.element.style.display="none");for(let x=0,m=g.children.length;x<m;x++)c(g.children[x])}function h(g,x,m){if(g.visible===!1){c(g);return}if(g.isCSS2DObject){rs.setFromMatrixPosition(g.matrixWorld),rs.applyMatrix4(Th);const f=rs.z>=-1&&rs.z<=1&&g.layers.test(m.layers)===!0,M=g.element;M.style.display=f===!0?"":"none",f===!0&&(g.onBeforeRender(t,x,m),M.style.transform="translate("+-100*g.center.x+"%,"+-100*g.center.y+"%)translate("+(rs.x*r+r)+"px,"+(-rs.y*a+a)+"px)",M.parentNode!==l&&l.appendChild(M),g.onAfterRender(t,x,m));const E={distanceToCameraSquared:d(m,g)};o.objects.set(g,E)}for(let f=0,M=g.children.length;f<M;f++)h(g.children[f],x,m)}function d(g,x){return Ah.setFromMatrixPosition(g.matrixWorld),Rh.setFromMatrixPosition(x.matrixWorld),Ah.distanceToSquared(Rh)}function u(g){const x=[];return g.traverseVisible(function(m){m.isCSS2DObject&&x.push(m)}),x}function p(g){const x=u(g).sort(function(f,M){if(f.renderOrder!==M.renderOrder)return M.renderOrder-f.renderOrder;const E=o.objects.get(f).distanceToCameraSquared,y=o.objects.get(M).distanceToCameraSquared;return E-y}),m=x.length;for(let f=0,M=x.length;f<M;f++)x[f].element.style.zIndex=m-f}}}var lt;(function(i){i.assertEqual=s=>{};function e(s){}i.assertIs=e;function t(s){throw new Error}i.assertNever=t,i.arrayToEnum=s=>{const r={};for(const a of s)r[a]=a;return r},i.getValidEnumValues=s=>{const r=i.objectKeys(s).filter(o=>typeof s[s[o]]!="number"),a={};for(const o of r)a[o]=s[o];return i.objectValues(a)},i.objectValues=s=>i.objectKeys(s).map(function(r){return s[r]}),i.objectKeys=typeof Object.keys=="function"?s=>Object.keys(s):s=>{const r=[];for(const a in s)Object.prototype.hasOwnProperty.call(s,a)&&r.push(a);return r},i.find=(s,r)=>{for(const a of s)if(r(a))return a},i.isInteger=typeof Number.isInteger=="function"?s=>Number.isInteger(s):s=>typeof s=="number"&&Number.isFinite(s)&&Math.floor(s)===s;function n(s,r=" | "){return s.map(a=>typeof a=="string"?`'${a}'`:a).join(r)}i.joinValues=n,i.jsonStringifyReplacer=(s,r)=>typeof r=="bigint"?r.toString():r})(lt||(lt={}));var Ch;(function(i){i.mergeShapes=(e,t)=>({...e,...t})})(Ch||(Ch={}));const Ee=lt.arrayToEnum(["string","nan","number","integer","float","boolean","date","bigint","symbol","function","undefined","null","array","object","unknown","promise","void","never","map","set"]),di=i=>{switch(typeof i){case"undefined":return Ee.undefined;case"string":return Ee.string;case"number":return Number.isNaN(i)?Ee.nan:Ee.number;case"boolean":return Ee.boolean;case"function":return Ee.function;case"bigint":return Ee.bigint;case"symbol":return Ee.symbol;case"object":return Array.isArray(i)?Ee.array:i===null?Ee.null:i.then&&typeof i.then=="function"&&i.catch&&typeof i.catch=="function"?Ee.promise:typeof Map<"u"&&i instanceof Map?Ee.map:typeof Set<"u"&&i instanceof Set?Ee.set:typeof Date<"u"&&i instanceof Date?Ee.date:Ee.object;default:return Ee.unknown}},se=lt.arrayToEnum(["invalid_type","invalid_literal","custom","invalid_union","invalid_union_discriminator","invalid_enum_value","unrecognized_keys","invalid_arguments","invalid_return_type","invalid_date","invalid_string","too_small","too_big","invalid_intersection_types","not_multiple_of","not_finite"]);class Jn extends Error{get errors(){return this.issues}constructor(e){super(),this.issues=[],this.addIssue=n=>{this.issues=[...this.issues,n]},this.addIssues=(n=[])=>{this.issues=[...this.issues,...n]};const t=new.target.prototype;Object.setPrototypeOf?Object.setPrototypeOf(this,t):this.__proto__=t,this.name="ZodError",this.issues=e}format(e){const t=e||function(r){return r.message},n={_errors:[]},s=r=>{for(const a of r.issues)if(a.code==="invalid_union")a.unionErrors.map(s);else if(a.code==="invalid_return_type")s(a.returnTypeError);else if(a.code==="invalid_arguments")s(a.argumentsError);else if(a.path.length===0)n._errors.push(t(a));else{let o=n,l=0;for(;l<a.path.length;){const c=a.path[l];l===a.path.length-1?(o[c]=o[c]||{_errors:[]},o[c]._errors.push(t(a))):o[c]=o[c]||{_errors:[]},o=o[c],l++}}};return s(this),n}static assert(e){if(!(e instanceof Jn))throw new Error(`Not a ZodError: ${e}`)}toString(){return this.message}get message(){return JSON.stringify(this.issues,lt.jsonStringifyReplacer,2)}get isEmpty(){return this.issues.length===0}flatten(e=t=>t.message){const t={},n=[];for(const s of this.issues)if(s.path.length>0){const r=s.path[0];t[r]=t[r]||[],t[r].push(e(s))}else n.push(e(s));return{formErrors:n,fieldErrors:t}}get formErrors(){return this.flatten()}}Jn.create=i=>new Jn(i);const gl=(i,e)=>{let t;switch(i.code){case se.invalid_type:i.received===Ee.undefined?t="Required":t=`Expected ${i.expected}, received ${i.received}`;break;case se.invalid_literal:t=`Invalid literal value, expected ${JSON.stringify(i.expected,lt.jsonStringifyReplacer)}`;break;case se.unrecognized_keys:t=`Unrecognized key(s) in object: ${lt.joinValues(i.keys,", ")}`;break;case se.invalid_union:t="Invalid input";break;case se.invalid_union_discriminator:t=`Invalid discriminator value. Expected ${lt.joinValues(i.options)}`;break;case se.invalid_enum_value:t=`Invalid enum value. Expected ${lt.joinValues(i.options)}, received '${i.received}'`;break;case se.invalid_arguments:t="Invalid function arguments";break;case se.invalid_return_type:t="Invalid function return type";break;case se.invalid_date:t="Invalid date";break;case se.invalid_string:typeof i.validation=="object"?"includes"in i.validation?(t=`Invalid input: must include "${i.validation.includes}"`,typeof i.validation.position=="number"&&(t=`${t} at one or more positions greater than or equal to ${i.validation.position}`)):"startsWith"in i.validation?t=`Invalid input: must start with "${i.validation.startsWith}"`:"endsWith"in i.validation?t=`Invalid input: must end with "${i.validation.endsWith}"`:lt.assertNever(i.validation):i.validation!=="regex"?t=`Invalid ${i.validation}`:t="Invalid";break;case se.too_small:i.type==="array"?t=`Array must contain ${i.exact?"exactly":i.inclusive?"at least":"more than"} ${i.minimum} element(s)`:i.type==="string"?t=`String must contain ${i.exact?"exactly":i.inclusive?"at least":"over"} ${i.minimum} character(s)`:i.type==="number"?t=`Number must be ${i.exact?"exactly equal to ":i.inclusive?"greater than or equal to ":"greater than "}${i.minimum}`:i.type==="bigint"?t=`Number must be ${i.exact?"exactly equal to ":i.inclusive?"greater than or equal to ":"greater than "}${i.minimum}`:i.type==="date"?t=`Date must be ${i.exact?"exactly equal to ":i.inclusive?"greater than or equal to ":"greater than "}${new Date(Number(i.minimum))}`:t="Invalid input";break;case se.too_big:i.type==="array"?t=`Array must contain ${i.exact?"exactly":i.inclusive?"at most":"less than"} ${i.maximum} element(s)`:i.type==="string"?t=`String must contain ${i.exact?"exactly":i.inclusive?"at most":"under"} ${i.maximum} character(s)`:i.type==="number"?t=`Number must be ${i.exact?"exactly":i.inclusive?"less than or equal to":"less than"} ${i.maximum}`:i.type==="bigint"?t=`BigInt must be ${i.exact?"exactly":i.inclusive?"less than or equal to":"less than"} ${i.maximum}`:i.type==="date"?t=`Date must be ${i.exact?"exactly":i.inclusive?"smaller than or equal to":"smaller than"} ${new Date(Number(i.maximum))}`:t="Invalid input";break;case se.custom:t="Invalid input";break;case se.invalid_intersection_types:t="Intersection results could not be merged";break;case se.not_multiple_of:t=`Number must be a multiple of ${i.multipleOf}`;break;case se.not_finite:t="Number must be finite";break;default:t=e.defaultError,lt.assertNever(i)}return{message:t}};let _v=gl;function vv(){return _v}const xv=i=>{const{data:e,path:t,errorMaps:n,issueData:s}=i,r=[...t,...s.path||[]],a={...s,path:r};if(s.message!==void 0)return{...s,path:r,message:s.message};let o="";const l=n.filter(c=>!!c).slice().reverse();for(const c of l)o=c(a,{data:e,defaultError:o}).message;return{...s,path:r,message:o}};function xe(i,e){const t=vv(),n=xv({issueData:e,data:i.data,path:i.path,errorMaps:[i.common.contextualErrorMap,i.schemaErrorMap,t,t===gl?void 0:gl].filter(s=>!!s)});i.common.issues.push(n)}class Qt{constructor(){this.value="valid"}dirty(){this.value==="valid"&&(this.value="dirty")}abort(){this.value!=="aborted"&&(this.value="aborted")}static mergeArray(e,t){const n=[];for(const s of t){if(s.status==="aborted")return We;s.status==="dirty"&&e.dirty(),n.push(s.value)}return{status:e.value,value:n}}static async mergeObjectAsync(e,t){const n=[];for(const s of t){const r=await s.key,a=await s.value;n.push({key:r,value:a})}return Qt.mergeObjectSync(e,n)}static mergeObjectSync(e,t){const n={};for(const s of t){const{key:r,value:a}=s;if(r.status==="aborted"||a.status==="aborted")return We;r.status==="dirty"&&e.dirty(),a.status==="dirty"&&e.dirty(),r.value!=="__proto__"&&(typeof a.value<"u"||s.alwaysSet)&&(n[r.value]=a.value)}return{status:e.value,value:n}}}const We=Object.freeze({status:"aborted"}),js=i=>({status:"dirty",value:i}),_n=i=>({status:"valid",value:i}),Ph=i=>i.status==="aborted",Lh=i=>i.status==="dirty",Es=i=>i.status==="valid",da=i=>typeof Promise<"u"&&i instanceof Promise;var Re;(function(i){i.errToObj=e=>typeof e=="string"?{message:e}:e||{},i.toString=e=>typeof e=="string"?e:e==null?void 0:e.message})(Re||(Re={}));class Fn{constructor(e,t,n,s){this._cachedPath=[],this.parent=e,this.data=t,this._path=n,this._key=s}get path(){return this._cachedPath.length||(Array.isArray(this._key)?this._cachedPath.push(...this._path,...this._key):this._cachedPath.push(...this._path,this._key)),this._cachedPath}}const Dh=(i,e)=>{if(Es(e))return{success:!0,data:e.value};if(!i.common.issues.length)throw new Error("Validation failed but no issues detected.");return{success:!1,get error(){if(this._error)return this._error;const t=new Jn(i.common.issues);return this._error=t,this._error}}};function Ke(i){if(!i)return{};const{errorMap:e,invalid_type_error:t,required_error:n,description:s}=i;if(e&&(t||n))throw new Error(`Can't use "invalid_type_error" or "required_error" in conjunction with custom error map.`);return e?{errorMap:e,description:s}:{errorMap:(a,o)=>{const{message:l}=i;return a.code==="invalid_enum_value"?{message:l??o.defaultError}:typeof o.data>"u"?{message:l??n??o.defaultError}:a.code!=="invalid_type"?{message:o.defaultError}:{message:l??t??o.defaultError}},description:s}}class nt{get description(){return this._def.description}_getType(e){return di(e.data)}_getOrReturnCtx(e,t){return t||{common:e.parent.common,data:e.data,parsedType:di(e.data),schemaErrorMap:this._def.errorMap,path:e.path,parent:e.parent}}_processInputParams(e){return{status:new Qt,ctx:{common:e.parent.common,data:e.data,parsedType:di(e.data),schemaErrorMap:this._def.errorMap,path:e.path,parent:e.parent}}}_parseSync(e){const t=this._parse(e);if(da(t))throw new Error("Synchronous parse encountered promise.");return t}_parseAsync(e){const t=this._parse(e);return Promise.resolve(t)}parse(e,t){const n=this.safeParse(e,t);if(n.success)return n.data;throw n.error}safeParse(e,t){const n={common:{issues:[],async:(t==null?void 0:t.async)??!1,contextualErrorMap:t==null?void 0:t.errorMap},path:(t==null?void 0:t.path)||[],schemaErrorMap:this._def.errorMap,parent:null,data:e,parsedType:di(e)},s=this._parseSync({data:e,path:n.path,parent:n});return Dh(n,s)}"~validate"(e){var n,s;const t={common:{issues:[],async:!!this["~standard"].async},path:[],schemaErrorMap:this._def.errorMap,parent:null,data:e,parsedType:di(e)};if(!this["~standard"].async)try{const r=this._parseSync({data:e,path:[],parent:t});return Es(r)?{value:r.value}:{issues:t.common.issues}}catch(r){(s=(n=r==null?void 0:r.message)==null?void 0:n.toLowerCase())!=null&&s.includes("encountered")&&(this["~standard"].async=!0),t.common={issues:[],async:!0}}return this._parseAsync({data:e,path:[],parent:t}).then(r=>Es(r)?{value:r.value}:{issues:t.common.issues})}async parseAsync(e,t){const n=await this.safeParseAsync(e,t);if(n.success)return n.data;throw n.error}async safeParseAsync(e,t){const n={common:{issues:[],contextualErrorMap:t==null?void 0:t.errorMap,async:!0},path:(t==null?void 0:t.path)||[],schemaErrorMap:this._def.errorMap,parent:null,data:e,parsedType:di(e)},s=this._parse({data:e,path:n.path,parent:n}),r=await(da(s)?s:Promise.resolve(s));return Dh(n,r)}refine(e,t){const n=s=>typeof t=="string"||typeof t>"u"?{message:t}:typeof t=="function"?t(s):t;return this._refinement((s,r)=>{const a=e(s),o=()=>r.addIssue({code:se.custom,...n(s)});return typeof Promise<"u"&&a instanceof Promise?a.then(l=>l?!0:(o(),!1)):a?!0:(o(),!1)})}refinement(e,t){return this._refinement((n,s)=>e(n)?!0:(s.addIssue(typeof t=="function"?t(n,s):t),!1))}_refinement(e){return new As({schema:this,typeName:Ge.ZodEffects,effect:{type:"refinement",refinement:e}})}superRefine(e){return this._refinement(e)}constructor(e){this.spa=this.safeParseAsync,this._def=e,this.parse=this.parse.bind(this),this.safeParse=this.safeParse.bind(this),this.parseAsync=this.parseAsync.bind(this),this.safeParseAsync=this.safeParseAsync.bind(this),this.spa=this.spa.bind(this),this.refine=this.refine.bind(this),this.refinement=this.refinement.bind(this),this.superRefine=this.superRefine.bind(this),this.optional=this.optional.bind(this),this.nullable=this.nullable.bind(this),this.nullish=this.nullish.bind(this),this.array=this.array.bind(this),this.promise=this.promise.bind(this),this.or=this.or.bind(this),this.and=this.and.bind(this),this.transform=this.transform.bind(this),this.brand=this.brand.bind(this),this.default=this.default.bind(this),this.catch=this.catch.bind(this),this.describe=this.describe.bind(this),this.pipe=this.pipe.bind(this),this.readonly=this.readonly.bind(this),this.isNullable=this.isNullable.bind(this),this.isOptional=this.isOptional.bind(this),this["~standard"]={version:1,vendor:"zod",validate:t=>this["~validate"](t)}}optional(){return _i.create(this,this._def)}nullable(){return Rs.create(this,this._def)}nullish(){return this.nullable().optional()}array(){return Un.create(this)}promise(){return _a.create(this,this._def)}or(e){return pa.create([this,e],this._def)}and(e){return ma.create(this,e,this._def)}transform(e){return new As({...Ke(this._def),schema:this,typeName:Ge.ZodEffects,effect:{type:"transform",transform:e}})}default(e){const t=typeof e=="function"?e:()=>e;return new yl({...Ke(this._def),innerType:this,defaultValue:t,typeName:Ge.ZodDefault})}brand(){return new Vv({typeName:Ge.ZodBranded,type:this,...Ke(this._def)})}catch(e){const t=typeof e=="function"?e:()=>e;return new bl({...Ke(this._def),innerType:this,catchValue:t,typeName:Ge.ZodCatch})}describe(e){const t=this.constructor;return new t({...this._def,description:e})}pipe(e){return Zl.create(this,e)}readonly(){return Ml.create(this)}isOptional(){return this.safeParse(void 0).success}isNullable(){return this.safeParse(null).success}}const yv=/^c[^\s-]{8,}$/i,bv=/^[0-9a-z]+$/,Mv=/^[0-9A-HJKMNP-TV-Z]{26}$/i,Sv=/^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$/i,Ev=/^[a-z0-9_-]{21}$/i,wv=/^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$/,Tv=/^[-+]?P(?!$)(?:(?:[-+]?\d+Y)|(?:[-+]?\d+[.,]\d+Y$))?(?:(?:[-+]?\d+M)|(?:[-+]?\d+[.,]\d+M$))?(?:(?:[-+]?\d+W)|(?:[-+]?\d+[.,]\d+W$))?(?:(?:[-+]?\d+D)|(?:[-+]?\d+[.,]\d+D$))?(?:T(?=[\d+-])(?:(?:[-+]?\d+H)|(?:[-+]?\d+[.,]\d+H$))?(?:(?:[-+]?\d+M)|(?:[-+]?\d+[.,]\d+M$))?(?:[-+]?\d+(?:[.,]\d+)?S)?)??$/,Av=/^(?!\.)(?!.*\.\.)([A-Z0-9_'+\-\.]*)[A-Z0-9_+-]@([A-Z0-9][A-Z0-9\-]*\.)+[A-Z]{2,}$/i,Rv="^(\\p{Extended_Pictographic}|\\p{Emoji_Component})+$";let ho;const Cv=/^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$/,Pv=/^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\/(3[0-2]|[12]?[0-9])$/,Lv=/^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/,Dv=/^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\/(12[0-8]|1[01][0-9]|[1-9]?[0-9])$/,Iv=/^([0-9a-zA-Z+/]{4})*(([0-9a-zA-Z+/]{2}==)|([0-9a-zA-Z+/]{3}=))?$/,Nv=/^([0-9a-zA-Z-_]{4})*(([0-9a-zA-Z-_]{2}(==)?)|([0-9a-zA-Z-_]{3}(=)?))?$/,ud="((\\d\\d[2468][048]|\\d\\d[13579][26]|\\d\\d0[48]|[02468][048]00|[13579][26]00)-02-29|\\d{4}-((0[13578]|1[02])-(0[1-9]|[12]\\d|3[01])|(0[469]|11)-(0[1-9]|[12]\\d|30)|(02)-(0[1-9]|1\\d|2[0-8])))",Uv=new RegExp(`^${ud}$`);function dd(i){let e="[0-5]\\d";i.precision?e=`${e}\\.\\d{${i.precision}}`:i.precision==null&&(e=`${e}(\\.\\d+)?`);const t=i.precision?"+":"?";return`([01]\\d|2[0-3]):[0-5]\\d(:${e})${t}`}function Ov(i){return new RegExp(`^${dd(i)}$`)}function Fv(i){let e=`${ud}T${dd(i)}`;const t=[];return t.push(i.local?"Z?":"Z"),i.offset&&t.push("([+-]\\d{2}:?\\d{2})"),e=`${e}(${t.join("|")})`,new RegExp(`^${e}$`)}function kv(i,e){return!!((e==="v4"||!e)&&Cv.test(i)||(e==="v6"||!e)&&Lv.test(i))}function Bv(i,e){if(!wv.test(i))return!1;try{const[t]=i.split(".");if(!t)return!1;const n=t.replace(/-/g,"+").replace(/_/g,"/").padEnd(t.length+(4-t.length%4)%4,"="),s=JSON.parse(atob(n));return!(typeof s!="object"||s===null||"typ"in s&&(s==null?void 0:s.typ)!=="JWT"||!s.alg||e&&s.alg!==e)}catch{return!1}}function zv(i,e){return!!((e==="v4"||!e)&&Pv.test(i)||(e==="v6"||!e)&&Dv.test(i))}class Xn extends nt{_parse(e){if(this._def.coerce&&(e.data=String(e.data)),this._getType(e)!==Ee.string){const r=this._getOrReturnCtx(e);return xe(r,{code:se.invalid_type,expected:Ee.string,received:r.parsedType}),We}const n=new Qt;let s;for(const r of this._def.checks)if(r.kind==="min")e.data.length<r.value&&(s=this._getOrReturnCtx(e,s),xe(s,{code:se.too_small,minimum:r.value,type:"string",inclusive:!0,exact:!1,message:r.message}),n.dirty());else if(r.kind==="max")e.data.length>r.value&&(s=this._getOrReturnCtx(e,s),xe(s,{code:se.too_big,maximum:r.value,type:"string",inclusive:!0,exact:!1,message:r.message}),n.dirty());else if(r.kind==="length"){const a=e.data.length>r.value,o=e.data.length<r.value;(a||o)&&(s=this._getOrReturnCtx(e,s),a?xe(s,{code:se.too_big,maximum:r.value,type:"string",inclusive:!0,exact:!0,message:r.message}):o&&xe(s,{code:se.too_small,minimum:r.value,type:"string",inclusive:!0,exact:!0,message:r.message}),n.dirty())}else if(r.kind==="email")Av.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"email",code:se.invalid_string,message:r.message}),n.dirty());else if(r.kind==="emoji")ho||(ho=new RegExp(Rv,"u")),ho.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"emoji",code:se.invalid_string,message:r.message}),n.dirty());else if(r.kind==="uuid")Sv.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"uuid",code:se.invalid_string,message:r.message}),n.dirty());else if(r.kind==="nanoid")Ev.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"nanoid",code:se.invalid_string,message:r.message}),n.dirty());else if(r.kind==="cuid")yv.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"cuid",code:se.invalid_string,message:r.message}),n.dirty());else if(r.kind==="cuid2")bv.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"cuid2",code:se.invalid_string,message:r.message}),n.dirty());else if(r.kind==="ulid")Mv.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"ulid",code:se.invalid_string,message:r.message}),n.dirty());else if(r.kind==="url")try{new URL(e.data)}catch{s=this._getOrReturnCtx(e,s),xe(s,{validation:"url",code:se.invalid_string,message:r.message}),n.dirty()}else r.kind==="regex"?(r.regex.lastIndex=0,r.regex.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"regex",code:se.invalid_string,message:r.message}),n.dirty())):r.kind==="trim"?e.data=e.data.trim():r.kind==="includes"?e.data.includes(r.value,r.position)||(s=this._getOrReturnCtx(e,s),xe(s,{code:se.invalid_string,validation:{includes:r.value,position:r.position},message:r.message}),n.dirty()):r.kind==="toLowerCase"?e.data=e.data.toLowerCase():r.kind==="toUpperCase"?e.data=e.data.toUpperCase():r.kind==="startsWith"?e.data.startsWith(r.value)||(s=this._getOrReturnCtx(e,s),xe(s,{code:se.invalid_string,validation:{startsWith:r.value},message:r.message}),n.dirty()):r.kind==="endsWith"?e.data.endsWith(r.value)||(s=this._getOrReturnCtx(e,s),xe(s,{code:se.invalid_string,validation:{endsWith:r.value},message:r.message}),n.dirty()):r.kind==="datetime"?Fv(r).test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{code:se.invalid_string,validation:"datetime",message:r.message}),n.dirty()):r.kind==="date"?Uv.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{code:se.invalid_string,validation:"date",message:r.message}),n.dirty()):r.kind==="time"?Ov(r).test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{code:se.invalid_string,validation:"time",message:r.message}),n.dirty()):r.kind==="duration"?Tv.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"duration",code:se.invalid_string,message:r.message}),n.dirty()):r.kind==="ip"?kv(e.data,r.version)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"ip",code:se.invalid_string,message:r.message}),n.dirty()):r.kind==="jwt"?Bv(e.data,r.alg)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"jwt",code:se.invalid_string,message:r.message}),n.dirty()):r.kind==="cidr"?zv(e.data,r.version)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"cidr",code:se.invalid_string,message:r.message}),n.dirty()):r.kind==="base64"?Iv.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"base64",code:se.invalid_string,message:r.message}),n.dirty()):r.kind==="base64url"?Nv.test(e.data)||(s=this._getOrReturnCtx(e,s),xe(s,{validation:"base64url",code:se.invalid_string,message:r.message}),n.dirty()):lt.assertNever(r);return{status:n.value,value:e.data}}_regex(e,t,n){return this.refinement(s=>e.test(s),{validation:t,code:se.invalid_string,...Re.errToObj(n)})}_addCheck(e){return new Xn({...this._def,checks:[...this._def.checks,e]})}email(e){return this._addCheck({kind:"email",...Re.errToObj(e)})}url(e){return this._addCheck({kind:"url",...Re.errToObj(e)})}emoji(e){return this._addCheck({kind:"emoji",...Re.errToObj(e)})}uuid(e){return this._addCheck({kind:"uuid",...Re.errToObj(e)})}nanoid(e){return this._addCheck({kind:"nanoid",...Re.errToObj(e)})}cuid(e){return this._addCheck({kind:"cuid",...Re.errToObj(e)})}cuid2(e){return this._addCheck({kind:"cuid2",...Re.errToObj(e)})}ulid(e){return this._addCheck({kind:"ulid",...Re.errToObj(e)})}base64(e){return this._addCheck({kind:"base64",...Re.errToObj(e)})}base64url(e){return this._addCheck({kind:"base64url",...Re.errToObj(e)})}jwt(e){return this._addCheck({kind:"jwt",...Re.errToObj(e)})}ip(e){return this._addCheck({kind:"ip",...Re.errToObj(e)})}cidr(e){return this._addCheck({kind:"cidr",...Re.errToObj(e)})}datetime(e){return typeof e=="string"?this._addCheck({kind:"datetime",precision:null,offset:!1,local:!1,message:e}):this._addCheck({kind:"datetime",precision:typeof(e==null?void 0:e.precision)>"u"?null:e==null?void 0:e.precision,offset:(e==null?void 0:e.offset)??!1,local:(e==null?void 0:e.local)??!1,...Re.errToObj(e==null?void 0:e.message)})}date(e){return this._addCheck({kind:"date",message:e})}time(e){return typeof e=="string"?this._addCheck({kind:"time",precision:null,message:e}):this._addCheck({kind:"time",precision:typeof(e==null?void 0:e.precision)>"u"?null:e==null?void 0:e.precision,...Re.errToObj(e==null?void 0:e.message)})}duration(e){return this._addCheck({kind:"duration",...Re.errToObj(e)})}regex(e,t){return this._addCheck({kind:"regex",regex:e,...Re.errToObj(t)})}includes(e,t){return this._addCheck({kind:"includes",value:e,position:t==null?void 0:t.position,...Re.errToObj(t==null?void 0:t.message)})}startsWith(e,t){return this._addCheck({kind:"startsWith",value:e,...Re.errToObj(t)})}endsWith(e,t){return this._addCheck({kind:"endsWith",value:e,...Re.errToObj(t)})}min(e,t){return this._addCheck({kind:"min",value:e,...Re.errToObj(t)})}max(e,t){return this._addCheck({kind:"max",value:e,...Re.errToObj(t)})}length(e,t){return this._addCheck({kind:"length",value:e,...Re.errToObj(t)})}nonempty(e){return this.min(1,Re.errToObj(e))}trim(){return new Xn({...this._def,checks:[...this._def.checks,{kind:"trim"}]})}toLowerCase(){return new Xn({...this._def,checks:[...this._def.checks,{kind:"toLowerCase"}]})}toUpperCase(){return new Xn({...this._def,checks:[...this._def.checks,{kind:"toUpperCase"}]})}get isDatetime(){return!!this._def.checks.find(e=>e.kind==="datetime")}get isDate(){return!!this._def.checks.find(e=>e.kind==="date")}get isTime(){return!!this._def.checks.find(e=>e.kind==="time")}get isDuration(){return!!this._def.checks.find(e=>e.kind==="duration")}get isEmail(){return!!this._def.checks.find(e=>e.kind==="email")}get isURL(){return!!this._def.checks.find(e=>e.kind==="url")}get isEmoji(){return!!this._def.checks.find(e=>e.kind==="emoji")}get isUUID(){return!!this._def.checks.find(e=>e.kind==="uuid")}get isNANOID(){return!!this._def.checks.find(e=>e.kind==="nanoid")}get isCUID(){return!!this._def.checks.find(e=>e.kind==="cuid")}get isCUID2(){return!!this._def.checks.find(e=>e.kind==="cuid2")}get isULID(){return!!this._def.checks.find(e=>e.kind==="ulid")}get isIP(){return!!this._def.checks.find(e=>e.kind==="ip")}get isCIDR(){return!!this._def.checks.find(e=>e.kind==="cidr")}get isBase64(){return!!this._def.checks.find(e=>e.kind==="base64")}get isBase64url(){return!!this._def.checks.find(e=>e.kind==="base64url")}get minLength(){let e=null;for(const t of this._def.checks)t.kind==="min"&&(e===null||t.value>e)&&(e=t.value);return e}get maxLength(){let e=null;for(const t of this._def.checks)t.kind==="max"&&(e===null||t.value<e)&&(e=t.value);return e}}Xn.create=i=>new Xn({checks:[],typeName:Ge.ZodString,coerce:(i==null?void 0:i.coerce)??!1,...Ke(i)});function Hv(i,e){const t=(i.toString().split(".")[1]||"").length,n=(e.toString().split(".")[1]||"").length,s=t>n?t:n,r=Number.parseInt(i.toFixed(s).replace(".","")),a=Number.parseInt(e.toFixed(s).replace(".",""));return r%a/10**s}class ws extends nt{constructor(){super(...arguments),this.min=this.gte,this.max=this.lte,this.step=this.multipleOf}_parse(e){if(this._def.coerce&&(e.data=Number(e.data)),this._getType(e)!==Ee.number){const r=this._getOrReturnCtx(e);return xe(r,{code:se.invalid_type,expected:Ee.number,received:r.parsedType}),We}let n;const s=new Qt;for(const r of this._def.checks)r.kind==="int"?lt.isInteger(e.data)||(n=this._getOrReturnCtx(e,n),xe(n,{code:se.invalid_type,expected:"integer",received:"float",message:r.message}),s.dirty()):r.kind==="min"?(r.inclusive?e.data<r.value:e.data<=r.value)&&(n=this._getOrReturnCtx(e,n),xe(n,{code:se.too_small,minimum:r.value,type:"number",inclusive:r.inclusive,exact:!1,message:r.message}),s.dirty()):r.kind==="max"?(r.inclusive?e.data>r.value:e.data>=r.value)&&(n=this._getOrReturnCtx(e,n),xe(n,{code:se.too_big,maximum:r.value,type:"number",inclusive:r.inclusive,exact:!1,message:r.message}),s.dirty()):r.kind==="multipleOf"?Hv(e.data,r.value)!==0&&(n=this._getOrReturnCtx(e,n),xe(n,{code:se.not_multiple_of,multipleOf:r.value,message:r.message}),s.dirty()):r.kind==="finite"?Number.isFinite(e.data)||(n=this._getOrReturnCtx(e,n),xe(n,{code:se.not_finite,message:r.message}),s.dirty()):lt.assertNever(r);return{status:s.value,value:e.data}}gte(e,t){return this.setLimit("min",e,!0,Re.toString(t))}gt(e,t){return this.setLimit("min",e,!1,Re.toString(t))}lte(e,t){return this.setLimit("max",e,!0,Re.toString(t))}lt(e,t){return this.setLimit("max",e,!1,Re.toString(t))}setLimit(e,t,n,s){return new ws({...this._def,checks:[...this._def.checks,{kind:e,value:t,inclusive:n,message:Re.toString(s)}]})}_addCheck(e){return new ws({...this._def,checks:[...this._def.checks,e]})}int(e){return this._addCheck({kind:"int",message:Re.toString(e)})}positive(e){return this._addCheck({kind:"min",value:0,inclusive:!1,message:Re.toString(e)})}negative(e){return this._addCheck({kind:"max",value:0,inclusive:!1,message:Re.toString(e)})}nonpositive(e){return this._addCheck({kind:"max",value:0,inclusive:!0,message:Re.toString(e)})}nonnegative(e){return this._addCheck({kind:"min",value:0,inclusive:!0,message:Re.toString(e)})}multipleOf(e,t){return this._addCheck({kind:"multipleOf",value:e,message:Re.toString(t)})}finite(e){return this._addCheck({kind:"finite",message:Re.toString(e)})}safe(e){return this._addCheck({kind:"min",inclusive:!0,value:Number.MIN_SAFE_INTEGER,message:Re.toString(e)})._addCheck({kind:"max",inclusive:!0,value:Number.MAX_SAFE_INTEGER,message:Re.toString(e)})}get minValue(){let e=null;for(const t of this._def.checks)t.kind==="min"&&(e===null||t.value>e)&&(e=t.value);return e}get maxValue(){let e=null;for(const t of this._def.checks)t.kind==="max"&&(e===null||t.value<e)&&(e=t.value);return e}get isInt(){return!!this._def.checks.find(e=>e.kind==="int"||e.kind==="multipleOf"&&lt.isInteger(e.value))}get isFinite(){let e=null,t=null;for(const n of this._def.checks){if(n.kind==="finite"||n.kind==="int"||n.kind==="multipleOf")return!0;n.kind==="min"?(t===null||n.value>t)&&(t=n.value):n.kind==="max"&&(e===null||n.value<e)&&(e=n.value)}return Number.isFinite(t)&&Number.isFinite(e)}}ws.create=i=>new ws({checks:[],typeName:Ge.ZodNumber,coerce:(i==null?void 0:i.coerce)||!1,...Ke(i)});class rr extends nt{constructor(){super(...arguments),this.min=this.gte,this.max=this.lte}_parse(e){if(this._def.coerce)try{e.data=BigInt(e.data)}catch{return this._getInvalidInput(e)}if(this._getType(e)!==Ee.bigint)return this._getInvalidInput(e);let n;const s=new Qt;for(const r of this._def.checks)r.kind==="min"?(r.inclusive?e.data<r.value:e.data<=r.value)&&(n=this._getOrReturnCtx(e,n),xe(n,{code:se.too_small,type:"bigint",minimum:r.value,inclusive:r.inclusive,message:r.message}),s.dirty()):r.kind==="max"?(r.inclusive?e.data>r.value:e.data>=r.value)&&(n=this._getOrReturnCtx(e,n),xe(n,{code:se.too_big,type:"bigint",maximum:r.value,inclusive:r.inclusive,message:r.message}),s.dirty()):r.kind==="multipleOf"?e.data%r.value!==BigInt(0)&&(n=this._getOrReturnCtx(e,n),xe(n,{code:se.not_multiple_of,multipleOf:r.value,message:r.message}),s.dirty()):lt.assertNever(r);return{status:s.value,value:e.data}}_getInvalidInput(e){const t=this._getOrReturnCtx(e);return xe(t,{code:se.invalid_type,expected:Ee.bigint,received:t.parsedType}),We}gte(e,t){return this.setLimit("min",e,!0,Re.toString(t))}gt(e,t){return this.setLimit("min",e,!1,Re.toString(t))}lte(e,t){return this.setLimit("max",e,!0,Re.toString(t))}lt(e,t){return this.setLimit("max",e,!1,Re.toString(t))}setLimit(e,t,n,s){return new rr({...this._def,checks:[...this._def.checks,{kind:e,value:t,inclusive:n,message:Re.toString(s)}]})}_addCheck(e){return new rr({...this._def,checks:[...this._def.checks,e]})}positive(e){return this._addCheck({kind:"min",value:BigInt(0),inclusive:!1,message:Re.toString(e)})}negative(e){return this._addCheck({kind:"max",value:BigInt(0),inclusive:!1,message:Re.toString(e)})}nonpositive(e){return this._addCheck({kind:"max",value:BigInt(0),inclusive:!0,message:Re.toString(e)})}nonnegative(e){return this._addCheck({kind:"min",value:BigInt(0),inclusive:!0,message:Re.toString(e)})}multipleOf(e,t){return this._addCheck({kind:"multipleOf",value:e,message:Re.toString(t)})}get minValue(){let e=null;for(const t of this._def.checks)t.kind==="min"&&(e===null||t.value>e)&&(e=t.value);return e}get maxValue(){let e=null;for(const t of this._def.checks)t.kind==="max"&&(e===null||t.value<e)&&(e=t.value);return e}}rr.create=i=>new rr({checks:[],typeName:Ge.ZodBigInt,coerce:(i==null?void 0:i.coerce)??!1,...Ke(i)});class _l extends nt{_parse(e){if(this._def.coerce&&(e.data=!!e.data),this._getType(e)!==Ee.boolean){const n=this._getOrReturnCtx(e);return xe(n,{code:se.invalid_type,expected:Ee.boolean,received:n.parsedType}),We}return _n(e.data)}}_l.create=i=>new _l({typeName:Ge.ZodBoolean,coerce:(i==null?void 0:i.coerce)||!1,...Ke(i)});class fa extends nt{_parse(e){if(this._def.coerce&&(e.data=new Date(e.data)),this._getType(e)!==Ee.date){const r=this._getOrReturnCtx(e);return xe(r,{code:se.invalid_type,expected:Ee.date,received:r.parsedType}),We}if(Number.isNaN(e.data.getTime())){const r=this._getOrReturnCtx(e);return xe(r,{code:se.invalid_date}),We}const n=new Qt;let s;for(const r of this._def.checks)r.kind==="min"?e.data.getTime()<r.value&&(s=this._getOrReturnCtx(e,s),xe(s,{code:se.too_small,message:r.message,inclusive:!0,exact:!1,minimum:r.value,type:"date"}),n.dirty()):r.kind==="max"?e.data.getTime()>r.value&&(s=this._getOrReturnCtx(e,s),xe(s,{code:se.too_big,message:r.message,inclusive:!0,exact:!1,maximum:r.value,type:"date"}),n.dirty()):lt.assertNever(r);return{status:n.value,value:new Date(e.data.getTime())}}_addCheck(e){return new fa({...this._def,checks:[...this._def.checks,e]})}min(e,t){return this._addCheck({kind:"min",value:e.getTime(),message:Re.toString(t)})}max(e,t){return this._addCheck({kind:"max",value:e.getTime(),message:Re.toString(t)})}get minDate(){let e=null;for(const t of this._def.checks)t.kind==="min"&&(e===null||t.value>e)&&(e=t.value);return e!=null?new Date(e):null}get maxDate(){let e=null;for(const t of this._def.checks)t.kind==="max"&&(e===null||t.value<e)&&(e=t.value);return e!=null?new Date(e):null}}fa.create=i=>new fa({checks:[],coerce:(i==null?void 0:i.coerce)||!1,typeName:Ge.ZodDate,...Ke(i)});class Ih extends nt{_parse(e){if(this._getType(e)!==Ee.symbol){const n=this._getOrReturnCtx(e);return xe(n,{code:se.invalid_type,expected:Ee.symbol,received:n.parsedType}),We}return _n(e.data)}}Ih.create=i=>new Ih({typeName:Ge.ZodSymbol,...Ke(i)});class Nh extends nt{_parse(e){if(this._getType(e)!==Ee.undefined){const n=this._getOrReturnCtx(e);return xe(n,{code:se.invalid_type,expected:Ee.undefined,received:n.parsedType}),We}return _n(e.data)}}Nh.create=i=>new Nh({typeName:Ge.ZodUndefined,...Ke(i)});class Uh extends nt{_parse(e){if(this._getType(e)!==Ee.null){const n=this._getOrReturnCtx(e);return xe(n,{code:se.invalid_type,expected:Ee.null,received:n.parsedType}),We}return _n(e.data)}}Uh.create=i=>new Uh({typeName:Ge.ZodNull,...Ke(i)});class Oh extends nt{constructor(){super(...arguments),this._any=!0}_parse(e){return _n(e.data)}}Oh.create=i=>new Oh({typeName:Ge.ZodAny,...Ke(i)});class Fh extends nt{constructor(){super(...arguments),this._unknown=!0}_parse(e){return _n(e.data)}}Fh.create=i=>new Fh({typeName:Ge.ZodUnknown,...Ke(i)});class yi extends nt{_parse(e){const t=this._getOrReturnCtx(e);return xe(t,{code:se.invalid_type,expected:Ee.never,received:t.parsedType}),We}}yi.create=i=>new yi({typeName:Ge.ZodNever,...Ke(i)});class kh extends nt{_parse(e){if(this._getType(e)!==Ee.undefined){const n=this._getOrReturnCtx(e);return xe(n,{code:se.invalid_type,expected:Ee.void,received:n.parsedType}),We}return _n(e.data)}}kh.create=i=>new kh({typeName:Ge.ZodVoid,...Ke(i)});class Un extends nt{_parse(e){const{ctx:t,status:n}=this._processInputParams(e),s=this._def;if(t.parsedType!==Ee.array)return xe(t,{code:se.invalid_type,expected:Ee.array,received:t.parsedType}),We;if(s.exactLength!==null){const a=t.data.length>s.exactLength.value,o=t.data.length<s.exactLength.value;(a||o)&&(xe(t,{code:a?se.too_big:se.too_small,minimum:o?s.exactLength.value:void 0,maximum:a?s.exactLength.value:void 0,type:"array",inclusive:!0,exact:!0,message:s.exactLength.message}),n.dirty())}if(s.minLength!==null&&t.data.length<s.minLength.value&&(xe(t,{code:se.too_small,minimum:s.minLength.value,type:"array",inclusive:!0,exact:!1,message:s.minLength.message}),n.dirty()),s.maxLength!==null&&t.data.length>s.maxLength.value&&(xe(t,{code:se.too_big,maximum:s.maxLength.value,type:"array",inclusive:!0,exact:!1,message:s.maxLength.message}),n.dirty()),t.common.async)return Promise.all([...t.data].map((a,o)=>s.type._parseAsync(new Fn(t,a,t.path,o)))).then(a=>Qt.mergeArray(n,a));const r=[...t.data].map((a,o)=>s.type._parseSync(new Fn(t,a,t.path,o)));return Qt.mergeArray(n,r)}get element(){return this._def.type}min(e,t){return new Un({...this._def,minLength:{value:e,message:Re.toString(t)}})}max(e,t){return new Un({...this._def,maxLength:{value:e,message:Re.toString(t)}})}length(e,t){return new Un({...this._def,exactLength:{value:e,message:Re.toString(t)}})}nonempty(e){return this.min(1,e)}}Un.create=(i,e)=>new Un({type:i,minLength:null,maxLength:null,exactLength:null,typeName:Ge.ZodArray,...Ke(e)});function hs(i){if(i instanceof Ot){const e={};for(const t in i.shape){const n=i.shape[t];e[t]=_i.create(hs(n))}return new Ot({...i._def,shape:()=>e})}else return i instanceof Un?new Un({...i._def,type:hs(i.element)}):i instanceof _i?_i.create(hs(i.unwrap())):i instanceof Rs?Rs.create(hs(i.unwrap())):i instanceof Bi?Bi.create(i.items.map(e=>hs(e))):i}class Ot extends nt{constructor(){super(...arguments),this._cached=null,this.nonstrict=this.passthrough,this.augment=this.extend}_getCached(){if(this._cached!==null)return this._cached;const e=this._def.shape(),t=lt.objectKeys(e);return this._cached={shape:e,keys:t},this._cached}_parse(e){if(this._getType(e)!==Ee.object){const c=this._getOrReturnCtx(e);return xe(c,{code:se.invalid_type,expected:Ee.object,received:c.parsedType}),We}const{status:n,ctx:s}=this._processInputParams(e),{shape:r,keys:a}=this._getCached(),o=[];if(!(this._def.catchall instanceof yi&&this._def.unknownKeys==="strip"))for(const c in s.data)a.includes(c)||o.push(c);const l=[];for(const c of a){const h=r[c],d=s.data[c];l.push({key:{status:"valid",value:c},value:h._parse(new Fn(s,d,s.path,c)),alwaysSet:c in s.data})}if(this._def.catchall instanceof yi){const c=this._def.unknownKeys;if(c==="passthrough")for(const h of o)l.push({key:{status:"valid",value:h},value:{status:"valid",value:s.data[h]}});else if(c==="strict")o.length>0&&(xe(s,{code:se.unrecognized_keys,keys:o}),n.dirty());else if(c!=="strip")throw new Error("Internal ZodObject error: invalid unknownKeys value.")}else{const c=this._def.catchall;for(const h of o){const d=s.data[h];l.push({key:{status:"valid",value:h},value:c._parse(new Fn(s,d,s.path,h)),alwaysSet:h in s.data})}}return s.common.async?Promise.resolve().then(async()=>{const c=[];for(const h of l){const d=await h.key,u=await h.value;c.push({key:d,value:u,alwaysSet:h.alwaysSet})}return c}).then(c=>Qt.mergeObjectSync(n,c)):Qt.mergeObjectSync(n,l)}get shape(){return this._def.shape()}strict(e){return Re.errToObj,new Ot({...this._def,unknownKeys:"strict",...e!==void 0?{errorMap:(t,n)=>{var r,a;const s=((a=(r=this._def).errorMap)==null?void 0:a.call(r,t,n).message)??n.defaultError;return t.code==="unrecognized_keys"?{message:Re.errToObj(e).message??s}:{message:s}}}:{}})}strip(){return new Ot({...this._def,unknownKeys:"strip"})}passthrough(){return new Ot({...this._def,unknownKeys:"passthrough"})}extend(e){return new Ot({...this._def,shape:()=>({...this._def.shape(),...e})})}merge(e){return new Ot({unknownKeys:e._def.unknownKeys,catchall:e._def.catchall,shape:()=>({...this._def.shape(),...e._def.shape()}),typeName:Ge.ZodObject})}setKey(e,t){return this.augment({[e]:t})}catchall(e){return new Ot({...this._def,catchall:e})}pick(e){const t={};for(const n of lt.objectKeys(e))e[n]&&this.shape[n]&&(t[n]=this.shape[n]);return new Ot({...this._def,shape:()=>t})}omit(e){const t={};for(const n of lt.objectKeys(this.shape))e[n]||(t[n]=this.shape[n]);return new Ot({...this._def,shape:()=>t})}deepPartial(){return hs(this)}partial(e){const t={};for(const n of lt.objectKeys(this.shape)){const s=this.shape[n];e&&!e[n]?t[n]=s:t[n]=s.optional()}return new Ot({...this._def,shape:()=>t})}required(e){const t={};for(const n of lt.objectKeys(this.shape))if(e&&!e[n])t[n]=this.shape[n];else{let r=this.shape[n];for(;r instanceof _i;)r=r._def.innerType;t[n]=r}return new Ot({...this._def,shape:()=>t})}keyof(){return fd(lt.objectKeys(this.shape))}}Ot.create=(i,e)=>new Ot({shape:()=>i,unknownKeys:"strip",catchall:yi.create(),typeName:Ge.ZodObject,...Ke(e)});Ot.strictCreate=(i,e)=>new Ot({shape:()=>i,unknownKeys:"strict",catchall:yi.create(),typeName:Ge.ZodObject,...Ke(e)});Ot.lazycreate=(i,e)=>new Ot({shape:i,unknownKeys:"strip",catchall:yi.create(),typeName:Ge.ZodObject,...Ke(e)});class pa extends nt{_parse(e){const{ctx:t}=this._processInputParams(e),n=this._def.options;function s(r){for(const o of r)if(o.result.status==="valid")return o.result;for(const o of r)if(o.result.status==="dirty")return t.common.issues.push(...o.ctx.common.issues),o.result;const a=r.map(o=>new Jn(o.ctx.common.issues));return xe(t,{code:se.invalid_union,unionErrors:a}),We}if(t.common.async)return Promise.all(n.map(async r=>{const a={...t,common:{...t.common,issues:[]},parent:null};return{result:await r._parseAsync({data:t.data,path:t.path,parent:a}),ctx:a}})).then(s);{let r;const a=[];for(const l of n){const c={...t,common:{...t.common,issues:[]},parent:null},h=l._parseSync({data:t.data,path:t.path,parent:c});if(h.status==="valid")return h;h.status==="dirty"&&!r&&(r={result:h,ctx:c}),c.common.issues.length&&a.push(c.common.issues)}if(r)return t.common.issues.push(...r.ctx.common.issues),r.result;const o=a.map(l=>new Jn(l));return xe(t,{code:se.invalid_union,unionErrors:o}),We}}get options(){return this._def.options}}pa.create=(i,e)=>new pa({options:i,typeName:Ge.ZodUnion,...Ke(e)});function vl(i,e){const t=di(i),n=di(e);if(i===e)return{valid:!0,data:i};if(t===Ee.object&&n===Ee.object){const s=lt.objectKeys(e),r=lt.objectKeys(i).filter(o=>s.indexOf(o)!==-1),a={...i,...e};for(const o of r){const l=vl(i[o],e[o]);if(!l.valid)return{valid:!1};a[o]=l.data}return{valid:!0,data:a}}else if(t===Ee.array&&n===Ee.array){if(i.length!==e.length)return{valid:!1};const s=[];for(let r=0;r<i.length;r++){const a=i[r],o=e[r],l=vl(a,o);if(!l.valid)return{valid:!1};s.push(l.data)}return{valid:!0,data:s}}else return t===Ee.date&&n===Ee.date&&+i==+e?{valid:!0,data:i}:{valid:!1}}class ma extends nt{_parse(e){const{status:t,ctx:n}=this._processInputParams(e),s=(r,a)=>{if(Ph(r)||Ph(a))return We;const o=vl(r.value,a.value);return o.valid?((Lh(r)||Lh(a))&&t.dirty(),{status:t.value,value:o.data}):(xe(n,{code:se.invalid_intersection_types}),We)};return n.common.async?Promise.all([this._def.left._parseAsync({data:n.data,path:n.path,parent:n}),this._def.right._parseAsync({data:n.data,path:n.path,parent:n})]).then(([r,a])=>s(r,a)):s(this._def.left._parseSync({data:n.data,path:n.path,parent:n}),this._def.right._parseSync({data:n.data,path:n.path,parent:n}))}}ma.create=(i,e,t)=>new ma({left:i,right:e,typeName:Ge.ZodIntersection,...Ke(t)});class Bi extends nt{_parse(e){const{status:t,ctx:n}=this._processInputParams(e);if(n.parsedType!==Ee.array)return xe(n,{code:se.invalid_type,expected:Ee.array,received:n.parsedType}),We;if(n.data.length<this._def.items.length)return xe(n,{code:se.too_small,minimum:this._def.items.length,inclusive:!0,exact:!1,type:"array"}),We;!this._def.rest&&n.data.length>this._def.items.length&&(xe(n,{code:se.too_big,maximum:this._def.items.length,inclusive:!0,exact:!1,type:"array"}),t.dirty());const r=[...n.data].map((a,o)=>{const l=this._def.items[o]||this._def.rest;return l?l._parse(new Fn(n,a,n.path,o)):null}).filter(a=>!!a);return n.common.async?Promise.all(r).then(a=>Qt.mergeArray(t,a)):Qt.mergeArray(t,r)}get items(){return this._def.items}rest(e){return new Bi({...this._def,rest:e})}}Bi.create=(i,e)=>{if(!Array.isArray(i))throw new Error("You must pass an array of schemas to z.tuple([ ... ])");return new Bi({items:i,typeName:Ge.ZodTuple,rest:null,...Ke(e)})};class ga extends nt{get keySchema(){return this._def.keyType}get valueSchema(){return this._def.valueType}_parse(e){const{status:t,ctx:n}=this._processInputParams(e);if(n.parsedType!==Ee.object)return xe(n,{code:se.invalid_type,expected:Ee.object,received:n.parsedType}),We;const s=[],r=this._def.keyType,a=this._def.valueType;for(const o in n.data)s.push({key:r._parse(new Fn(n,o,n.path,o)),value:a._parse(new Fn(n,n.data[o],n.path,o)),alwaysSet:o in n.data});return n.common.async?Qt.mergeObjectAsync(t,s):Qt.mergeObjectSync(t,s)}get element(){return this._def.valueType}static create(e,t,n){return t instanceof nt?new ga({keyType:e,valueType:t,typeName:Ge.ZodRecord,...Ke(n)}):new ga({keyType:Xn.create(),valueType:e,typeName:Ge.ZodRecord,...Ke(t)})}}class Bh extends nt{get keySchema(){return this._def.keyType}get valueSchema(){return this._def.valueType}_parse(e){const{status:t,ctx:n}=this._processInputParams(e);if(n.parsedType!==Ee.map)return xe(n,{code:se.invalid_type,expected:Ee.map,received:n.parsedType}),We;const s=this._def.keyType,r=this._def.valueType,a=[...n.data.entries()].map(([o,l],c)=>({key:s._parse(new Fn(n,o,n.path,[c,"key"])),value:r._parse(new Fn(n,l,n.path,[c,"value"]))}));if(n.common.async){const o=new Map;return Promise.resolve().then(async()=>{for(const l of a){const c=await l.key,h=await l.value;if(c.status==="aborted"||h.status==="aborted")return We;(c.status==="dirty"||h.status==="dirty")&&t.dirty(),o.set(c.value,h.value)}return{status:t.value,value:o}})}else{const o=new Map;for(const l of a){const c=l.key,h=l.value;if(c.status==="aborted"||h.status==="aborted")return We;(c.status==="dirty"||h.status==="dirty")&&t.dirty(),o.set(c.value,h.value)}return{status:t.value,value:o}}}}Bh.create=(i,e,t)=>new Bh({valueType:e,keyType:i,typeName:Ge.ZodMap,...Ke(t)});class ar extends nt{_parse(e){const{status:t,ctx:n}=this._processInputParams(e);if(n.parsedType!==Ee.set)return xe(n,{code:se.invalid_type,expected:Ee.set,received:n.parsedType}),We;const s=this._def;s.minSize!==null&&n.data.size<s.minSize.value&&(xe(n,{code:se.too_small,minimum:s.minSize.value,type:"set",inclusive:!0,exact:!1,message:s.minSize.message}),t.dirty()),s.maxSize!==null&&n.data.size>s.maxSize.value&&(xe(n,{code:se.too_big,maximum:s.maxSize.value,type:"set",inclusive:!0,exact:!1,message:s.maxSize.message}),t.dirty());const r=this._def.valueType;function a(l){const c=new Set;for(const h of l){if(h.status==="aborted")return We;h.status==="dirty"&&t.dirty(),c.add(h.value)}return{status:t.value,value:c}}const o=[...n.data.values()].map((l,c)=>r._parse(new Fn(n,l,n.path,c)));return n.common.async?Promise.all(o).then(l=>a(l)):a(o)}min(e,t){return new ar({...this._def,minSize:{value:e,message:Re.toString(t)}})}max(e,t){return new ar({...this._def,maxSize:{value:e,message:Re.toString(t)}})}size(e,t){return this.min(e,t).max(e,t)}nonempty(e){return this.min(1,e)}}ar.create=(i,e)=>new ar({valueType:i,minSize:null,maxSize:null,typeName:Ge.ZodSet,...Ke(e)});class zh extends nt{get schema(){return this._def.getter()}_parse(e){const{ctx:t}=this._processInputParams(e);return this._def.getter()._parse({data:t.data,path:t.path,parent:t})}}zh.create=(i,e)=>new zh({getter:i,typeName:Ge.ZodLazy,...Ke(e)});class xl extends nt{_parse(e){if(e.data!==this._def.value){const t=this._getOrReturnCtx(e);return xe(t,{received:t.data,code:se.invalid_literal,expected:this._def.value}),We}return{status:"valid",value:e.data}}get value(){return this._def.value}}xl.create=(i,e)=>new xl({value:i,typeName:Ge.ZodLiteral,...Ke(e)});function fd(i,e){return new Ts({values:i,typeName:Ge.ZodEnum,...Ke(e)})}class Ts extends nt{_parse(e){if(typeof e.data!="string"){const t=this._getOrReturnCtx(e),n=this._def.values;return xe(t,{expected:lt.joinValues(n),received:t.parsedType,code:se.invalid_type}),We}if(this._cache||(this._cache=new Set(this._def.values)),!this._cache.has(e.data)){const t=this._getOrReturnCtx(e),n=this._def.values;return xe(t,{received:t.data,code:se.invalid_enum_value,options:n}),We}return _n(e.data)}get options(){return this._def.values}get enum(){const e={};for(const t of this._def.values)e[t]=t;return e}get Values(){const e={};for(const t of this._def.values)e[t]=t;return e}get Enum(){const e={};for(const t of this._def.values)e[t]=t;return e}extract(e,t=this._def){return Ts.create(e,{...this._def,...t})}exclude(e,t=this._def){return Ts.create(this.options.filter(n=>!e.includes(n)),{...this._def,...t})}}Ts.create=fd;class Hh extends nt{_parse(e){const t=lt.getValidEnumValues(this._def.values),n=this._getOrReturnCtx(e);if(n.parsedType!==Ee.string&&n.parsedType!==Ee.number){const s=lt.objectValues(t);return xe(n,{expected:lt.joinValues(s),received:n.parsedType,code:se.invalid_type}),We}if(this._cache||(this._cache=new Set(lt.getValidEnumValues(this._def.values))),!this._cache.has(e.data)){const s=lt.objectValues(t);return xe(n,{received:n.data,code:se.invalid_enum_value,options:s}),We}return _n(e.data)}get enum(){return this._def.values}}Hh.create=(i,e)=>new Hh({values:i,typeName:Ge.ZodNativeEnum,...Ke(e)});class _a extends nt{unwrap(){return this._def.type}_parse(e){const{ctx:t}=this._processInputParams(e);if(t.parsedType!==Ee.promise&&t.common.async===!1)return xe(t,{code:se.invalid_type,expected:Ee.promise,received:t.parsedType}),We;const n=t.parsedType===Ee.promise?t.data:Promise.resolve(t.data);return _n(n.then(s=>this._def.type.parseAsync(s,{path:t.path,errorMap:t.common.contextualErrorMap})))}}_a.create=(i,e)=>new _a({type:i,typeName:Ge.ZodPromise,...Ke(e)});class As extends nt{innerType(){return this._def.schema}sourceType(){return this._def.schema._def.typeName===Ge.ZodEffects?this._def.schema.sourceType():this._def.schema}_parse(e){const{status:t,ctx:n}=this._processInputParams(e),s=this._def.effect||null,r={addIssue:a=>{xe(n,a),a.fatal?t.abort():t.dirty()},get path(){return n.path}};if(r.addIssue=r.addIssue.bind(r),s.type==="preprocess"){const a=s.transform(n.data,r);if(n.common.async)return Promise.resolve(a).then(async o=>{if(t.value==="aborted")return We;const l=await this._def.schema._parseAsync({data:o,path:n.path,parent:n});return l.status==="aborted"?We:l.status==="dirty"||t.value==="dirty"?js(l.value):l});{if(t.value==="aborted")return We;const o=this._def.schema._parseSync({data:a,path:n.path,parent:n});return o.status==="aborted"?We:o.status==="dirty"||t.value==="dirty"?js(o.value):o}}if(s.type==="refinement"){const a=o=>{const l=s.refinement(o,r);if(n.common.async)return Promise.resolve(l);if(l instanceof Promise)throw new Error("Async refinement encountered during synchronous parse operation. Use .parseAsync instead.");return o};if(n.common.async===!1){const o=this._def.schema._parseSync({data:n.data,path:n.path,parent:n});return o.status==="aborted"?We:(o.status==="dirty"&&t.dirty(),a(o.value),{status:t.value,value:o.value})}else return this._def.schema._parseAsync({data:n.data,path:n.path,parent:n}).then(o=>o.status==="aborted"?We:(o.status==="dirty"&&t.dirty(),a(o.value).then(()=>({status:t.value,value:o.value}))))}if(s.type==="transform")if(n.common.async===!1){const a=this._def.schema._parseSync({data:n.data,path:n.path,parent:n});if(!Es(a))return We;const o=s.transform(a.value,r);if(o instanceof Promise)throw new Error("Asynchronous transform encountered during synchronous parse operation. Use .parseAsync instead.");return{status:t.value,value:o}}else return this._def.schema._parseAsync({data:n.data,path:n.path,parent:n}).then(a=>Es(a)?Promise.resolve(s.transform(a.value,r)).then(o=>({status:t.value,value:o})):We);lt.assertNever(s)}}As.create=(i,e,t)=>new As({schema:i,typeName:Ge.ZodEffects,effect:e,...Ke(t)});As.createWithPreprocess=(i,e,t)=>new As({schema:e,effect:{type:"preprocess",transform:i},typeName:Ge.ZodEffects,...Ke(t)});class _i extends nt{_parse(e){return this._getType(e)===Ee.undefined?_n(void 0):this._def.innerType._parse(e)}unwrap(){return this._def.innerType}}_i.create=(i,e)=>new _i({innerType:i,typeName:Ge.ZodOptional,...Ke(e)});class Rs extends nt{_parse(e){return this._getType(e)===Ee.null?_n(null):this._def.innerType._parse(e)}unwrap(){return this._def.innerType}}Rs.create=(i,e)=>new Rs({innerType:i,typeName:Ge.ZodNullable,...Ke(e)});class yl extends nt{_parse(e){const{ctx:t}=this._processInputParams(e);let n=t.data;return t.parsedType===Ee.undefined&&(n=this._def.defaultValue()),this._def.innerType._parse({data:n,path:t.path,parent:t})}removeDefault(){return this._def.innerType}}yl.create=(i,e)=>new yl({innerType:i,typeName:Ge.ZodDefault,defaultValue:typeof e.default=="function"?e.default:()=>e.default,...Ke(e)});class bl extends nt{_parse(e){const{ctx:t}=this._processInputParams(e),n={...t,common:{...t.common,issues:[]}},s=this._def.innerType._parse({data:n.data,path:n.path,parent:{...n}});return da(s)?s.then(r=>({status:"valid",value:r.status==="valid"?r.value:this._def.catchValue({get error(){return new Jn(n.common.issues)},input:n.data})})):{status:"valid",value:s.status==="valid"?s.value:this._def.catchValue({get error(){return new Jn(n.common.issues)},input:n.data})}}removeCatch(){return this._def.innerType}}bl.create=(i,e)=>new bl({innerType:i,typeName:Ge.ZodCatch,catchValue:typeof e.catch=="function"?e.catch:()=>e.catch,...Ke(e)});class Vh extends nt{_parse(e){if(this._getType(e)!==Ee.nan){const n=this._getOrReturnCtx(e);return xe(n,{code:se.invalid_type,expected:Ee.nan,received:n.parsedType}),We}return{status:"valid",value:e.data}}}Vh.create=i=>new Vh({typeName:Ge.ZodNaN,...Ke(i)});class Vv extends nt{_parse(e){const{ctx:t}=this._processInputParams(e),n=t.data;return this._def.type._parse({data:n,path:t.path,parent:t})}unwrap(){return this._def.type}}class Zl extends nt{_parse(e){const{status:t,ctx:n}=this._processInputParams(e);if(n.common.async)return(async()=>{const r=await this._def.in._parseAsync({data:n.data,path:n.path,parent:n});return r.status==="aborted"?We:r.status==="dirty"?(t.dirty(),js(r.value)):this._def.out._parseAsync({data:r.value,path:n.path,parent:n})})();{const s=this._def.in._parseSync({data:n.data,path:n.path,parent:n});return s.status==="aborted"?We:s.status==="dirty"?(t.dirty(),{status:"dirty",value:s.value}):this._def.out._parseSync({data:s.value,path:n.path,parent:n})}}static create(e,t){return new Zl({in:e,out:t,typeName:Ge.ZodPipeline})}}class Ml extends nt{_parse(e){const t=this._def.innerType._parse(e),n=s=>(Es(s)&&(s.value=Object.freeze(s.value)),s);return da(t)?t.then(s=>n(s)):n(t)}unwrap(){return this._def.innerType}}Ml.create=(i,e)=>new Ml({innerType:i,typeName:Ge.ZodReadonly,...Ke(e)});var Ge;(function(i){i.ZodString="ZodString",i.ZodNumber="ZodNumber",i.ZodNaN="ZodNaN",i.ZodBigInt="ZodBigInt",i.ZodBoolean="ZodBoolean",i.ZodDate="ZodDate",i.ZodSymbol="ZodSymbol",i.ZodUndefined="ZodUndefined",i.ZodNull="ZodNull",i.ZodAny="ZodAny",i.ZodUnknown="ZodUnknown",i.ZodNever="ZodNever",i.ZodVoid="ZodVoid",i.ZodArray="ZodArray",i.ZodObject="ZodObject",i.ZodUnion="ZodUnion",i.ZodDiscriminatedUnion="ZodDiscriminatedUnion",i.ZodIntersection="ZodIntersection",i.ZodTuple="ZodTuple",i.ZodRecord="ZodRecord",i.ZodMap="ZodMap",i.ZodSet="ZodSet",i.ZodFunction="ZodFunction",i.ZodLazy="ZodLazy",i.ZodLiteral="ZodLiteral",i.ZodEnum="ZodEnum",i.ZodEffects="ZodEffects",i.ZodNativeEnum="ZodNativeEnum",i.ZodOptional="ZodOptional",i.ZodNullable="ZodNullable",i.ZodDefault="ZodDefault",i.ZodCatch="ZodCatch",i.ZodPromise="ZodPromise",i.ZodBranded="ZodBranded",i.ZodPipeline="ZodPipeline",i.ZodReadonly="ZodReadonly"})(Ge||(Ge={}));const ie=Xn.create,we=ws.create,dr=_l.create;yi.create;const tt=Un.create,rt=Ot.create;pa.create;ma.create;const va=Bi.create,uo=ga.create,Cs=xl.create,Oi=Ts.create;_a.create;_i.create;Rs.create;const pd="database-tycoon.city",md=1,Gv=rt({min_x:we().int(),min_y:we().int(),max_x:we().int(),max_y:we().int()}),Wv=rt({schema:ie(),x:we().int(),y:we().int(),w:we().int().positive(),h:we().int().positive()}),$v=rt({object_key:ie(),x:we().int(),y:we().int(),w:we().int().min(1),h:we().int().min(1),zone_style:Oi(["industrial","commercial","residential"]),target_density:we().int().min(1).max(8),powered:dr(),last_build_age_s:we().nullable(),build_status:ie().nullable(),test_status:ie().nullable(),freshness_status:ie().nullable(),schema_drift_age_s:we().nullable()}),Xv=rt({source:ie(),runs_seen:we().int().nonnegative(),window_days:we().nonnegative(),rate_per_day:we().nullable()}),qv=rt({name:ie(),primary_key:tt(ie()).optional().default([]),unique_keys:tt(tt(ie())).optional().default([]),instructions:ie().nullable().optional().default(null),synonyms:tt(ie()).optional().default([]),example_queries:tt(ie()).optional().default([])}),Yv=rt({key:ie(),schema:ie(),name:ie(),kind:Oi(["table","view"]),row_count:we().int().nonnegative(),columns:tt(rt({name:ie(),type:ie(),description:ie().nullable(),test_status:ie().nullable()})),dbt:rt({description:ie(),materialized:ie(),tags:tt(ie()),owner:ie().nullable(),tests:tt(rt({name:ie(),column:ie().nullable(),status:ie().nullable()}))}).nullable(),usage:Xv.nullable().optional().default(null),semantic:qv.nullable().optional().default(null)}),Zv=rt({src:ie(),dst:ie(),rate:we().min(0).max(1),provenance:Oi(["manifest","duckdb","view_sql"]),route:tt(va([we().int(),we().int()])),columns:tt(va([ie(),ie()])),daily_load_s:we().nullable()}),Kv=rt({name:ie(),many:ie(),one:ie(),cardinality:ie(),keys:tt(va([ie(),ie()])),composite:dr(),provenance:ie(),lineage_edge:va([ie(),ie()]).nullable().optional().default(null)}),Sl={manifest:"declared (dbt)",duckdb:"declared (duckdb)",view_sql:"inferred (SQL scan)"},jv=rt({kind:ie(),x:we().int(),y:we().int(),facing:Oi(["n","e","s","w"]).nullable(),w:we().int().positive(),h:we().int().positive()}),Jv=rt({engine:ie(),currency:ie(),unit_price_per_s:we().nonnegative(),price_source:ie(),daily_load_s:we().nullable(),daily_cost:we().nullable(),priced_objects:we().int().nonnegative(),unpriced_objects:we().int().nonnegative(),by_object:tt(rt({object_key:ie(),daily_load_s:we(),daily_cost:we()})),note:ie()}),Qv=rt({schema:ie(),condition:ie(),worst_source:ie().nullable(),verdict:ie().nullable(),hops:we().int().nullable()}),ex=rt({cells:tt(Qv),note:ie()}),tx=rt({id:ie(),name:ie(),description:ie(),state:ie(),met:dr().nullable(),have:we().int().nullable(),need:we().int().nullable(),short:tt(ie()),note:ie()}),nx=rt({milestones:tt(tx),note:ie()}),ix=rt({span_ticks:we().int().positive(),note:ie(),steps:tt(rt({object_key:ie(),start:we().int().nonnegative(),duration:we().int().positive()}))}),gd=rt({format:Cs(pd),version:Cs(md),database:rt({name:ie(),object_count:we().int().nonnegative(),total_rows:we().int().nonnegative(),has_known_edges:dr(),notes:tt(ie())}),grid:rt({width:we().int().positive(),height:we().int().positive(),tile_kinds:tt(ie()),tiles_rle:tt(we().int().nonnegative())}),plant:rt({x:we().int(),y:we().int()}),focus:Gv,districts:tt(Wv),lots:tt($v),objects:tt(Yv),edges:tt(Zv),joins:tt(Kv).optional().default([]),budget:Jv.nullable().optional().default(null),weather:ex.nullable().optional().default(null),street_features:tt(jv).optional().default([]),achievements:nx.optional().default({milestones:[],note:""}),library:rt({x:we().int(),y:we().int()}).nullable(),firehouse:rt({x:we().int(),y:we().int()}).nullable(),replay:ix.nullable(),theme:rt({name:ie(),logo_text:ie(),labels:uo(ie(),ie()),colors:uo(ie(),tt(we())),sprites:uo(ie(),tt(we())),spritesheet:ie()})}),_d=rt({request_id:ie().uuid(),citizen_id:ie(),timestamp:ie().datetime(),priority:Oi(["LOW","MEDIUM","HIGH","CRITICAL"]),request_type:Oi(["DATA_SOURCE","SCHEMA_CHANGE","QUALITY_FIX","PERFORMANCE"]),description:ie(),status:Oi(["PENDING","IN_PROGRESS","FULFILLED","EXPIRED"]),complexity:we().int().min(1).max(10)});function wa(i,e){return i.achievements.milestones.find(t=>t.id===e)??null}function El(i){return i.joins.length>0||i.objects.some(e=>e.semantic!==null)}function vd(i,e){return i.joins.filter(t=>t.many===e||t.one===e).map(t=>t.many===e?{join:t,other:t.one,side:"many"}:{join:t,other:t.many,side:"one"})}function Kl(i){const e=i.toUpperCase();return/INT|DECIMAL|NUMERIC|DOUBLE|FLOAT|REAL|HUGE/.test(e)?"numeric":/CHAR|TEXT|STRING|UUID/.test(e)?"text":/DATE|TIME/.test(e)?"temporal":/BOOL/.test(e)?"boolean":/JSON|STRUCT|LIST|MAP|ARRAY|UNION/.test(e)?"nested":"other"}function Us(i,e,t){if(i.length%2!==0)throw new Error(`tiles_rle must hold (kind, run) pairs; got ${i.length} numbers`);const n=new Uint8Array(e*t);let s=0;for(let r=0;r<i.length;r+=2){const a=i[r],o=i[r+1];if(o<1)throw new Error(`run length must be positive; got ${o}`);if(s+o>n.length)throw new Error(`tiles_rle decodes past ${n.length} cells`);n.fill(a,s,s+=o)}if(s!==n.length)throw new Error(`tiles_rle decodes to ${s} cells, expected ${n.length}`);return n}async function xd(i){const e=await fetch(i);if(!e.ok)throw new Error(`fetching ${i}: HTTP ${e.status}`);return gd.parse(await e.json())}function yd(i,e){return{upstream:i.edges.filter(t=>t.dst===e).map(t=>({key:t.src,provenance:t.provenance})),downstream:i.edges.filter(t=>t.src===e).map(t=>({key:t.dst,provenance:t.provenance}))}}const sx=Object.freeze(Object.defineProperty({__proto__:null,FORMAT:pd,PROVENANCE_LABEL:Sl,VERSION:md,citySchema:gd,decodeRle:Us,hasSemanticModel:El,joinsOf:vd,lineageOf:yd,loadCity:xd,milestoneOf:wa,requestSchema:_d,typeFamily:Kl},Symbol.toStringTag,{value:"Module"})),rx=[[1,0],[0,-1],[0,1],[-1,0]];class bd{constructor(e){Q(this,"drivable");Q(this,"width");Q(this,"height");this.width=e.grid.width,this.height=e.grid.height;const t=Us(e.grid.tiles_rle,this.width,this.height),n=new Set(["road","lot","power_line"].map(s=>e.grid.tile_kinds.indexOf(s)).filter(s=>s>=0));this.drivable=new Uint8Array(t.length);for(let s=0;s<t.length;s+=1)this.drivable[s]=n.has(t[s])?1:0}isDrivable(e,t){return e>=0&&t>=0&&e<this.width&&t<this.height&&this.drivable[t*this.width+e]===1}path(e,t){const n=new Set(t.map(([c,h])=>`${c},${h}`));if(!n.size)return null;const s=c=>`${c[0]},${c[1]}`;if(n.has(s(e)))return[e];const r=new Map([[s(e),e]]),a=[e];let o=null;for(;a.length&&!o;){const[c,h]=a.shift();for(const[d,u]of rx){const p=[c+d,h+u],g=s(p);if(!(r.has(g)||!this.isDrivable(p[0],p[1]))){if(r.set(g,[c,h]),n.has(g)){o=p;break}a.push(p)}}}if(!o)return null;const l=[o];for(;s(l[l.length-1])!==s(e);)l.push(r.get(s(l[l.length-1])));return l.reverse()}}const ax=48,ox=.35,lx=14*86400;class cx{constructor(e,t){Q(this,"guests",[]);Q(this,"weights");Q(this,"plant");Q(this,"routes",new Map);this.doc=e,this.rng=t,this.plant=[e.plant.x,e.plant.y];const n=new bd(e);this.weights=e.lots.filter(s=>s.powered).map(s=>{const r=s.last_build_age_s!==null?.5**(s.last_build_age_s/lx):1;return{lot:s,weight:s.target_density*r}}).filter(s=>s.weight>0).filter(s=>{const r=n.path(this.plant,[[s.lot.x,s.lot.y]]);return r&&this.routes.set(s.lot.object_key,r),r!==null})}tick(){let e=0;for(const t of this.guests){if(t.progress+=1,t.progress<t.path.length){this.guests[e++]=t;continue}t.returning||(this.turnBack(t),this.guests[e++]=t)}if(this.guests.length=e,!(this.weights.length===0||this.guests.length>=ax)&&this.rng()<ox){const t=this.pick();t&&this.guests.push({path:this.routes.get(t.object_key),progress:0,targetKey:t.object_key,happy:!0,returning:!1})}}pick(){var n;const e=this.weights.reduce((s,r)=>s+r.weight,0);let t=this.rng()*e;for(const{lot:s,weight:r}of this.weights)if(t-=r,t<=0)return s;return((n=this.weights.at(-1))==null?void 0:n.lot)??null}turnBack(e){const t=this.doc.lots.find(n=>n.object_key===e.targetKey);e.happy=!((t==null?void 0:t.test_status)==="fail"||(t==null?void 0:t.build_status)==="error"),e.returning=!0,e.path=[...e.path].reverse(),e.progress=0}}const hx={type:"change"},Gh=1e-6,Wh=new Sn;class ux extends nd{constructor(e,t=null){super(e,t),this.movementSpeed=1,this.rollSpeed=.005,this.dragToLook=!1,this.autoForward=!1,this._moveState={up:0,down:0,left:0,right:0,forward:0,back:0,pitchUp:0,pitchDown:0,yawLeft:0,yawRight:0,rollLeft:0,rollRight:0},this._moveVector=new P(0,0,0),this._rotationVector=new P(0,0,0),this._lastQuaternion=new Sn,this._lastPosition=new P,this._status=0,this._onKeyDown=dx.bind(this),this._onKeyUp=fx.bind(this),this._onPointerMove=mx.bind(this),this._onPointerDown=px.bind(this),this._onPointerUp=gx.bind(this),this._onPointerCancel=_x.bind(this),this._onContextMenu=vx.bind(this),t!==null&&this.connect(t)}connect(e){super.connect(e),window.addEventListener("keydown",this._onKeyDown),window.addEventListener("keyup",this._onKeyUp),this.domElement.addEventListener("pointermove",this._onPointerMove),this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointerup",this._onPointerUp),this.domElement.addEventListener("pointercancel",this._onPointerCancel),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.style.touchAction="none"}disconnect(){window.removeEventListener("keydown",this._onKeyDown),window.removeEventListener("keyup",this._onKeyUp),this.domElement.removeEventListener("pointermove",this._onPointerMove),this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerCancel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.domElement.style.touchAction=""}dispose(){this.disconnect()}update(e){if(this.enabled===!1)return;const t=this.object,n=e*this.movementSpeed,s=e*this.rollSpeed;t.translateX(this._moveVector.x*n),t.translateY(this._moveVector.y*n),t.translateZ(this._moveVector.z*n),Wh.set(this._rotationVector.x*s,this._rotationVector.y*s,this._rotationVector.z*s,1).normalize(),t.quaternion.multiply(Wh),(this._lastPosition.distanceToSquared(t.position)>Gh||8*(1-this._lastQuaternion.dot(t.quaternion))>Gh)&&(this.dispatchEvent(hx),this._lastQuaternion.copy(t.quaternion),this._lastPosition.copy(t.position))}_updateMovementVector(){const e=this._moveState.forward||this.autoForward&&!this._moveState.back?1:0;this._moveVector.x=-this._moveState.left+this._moveState.right,this._moveVector.y=-this._moveState.down+this._moveState.up,this._moveVector.z=-e+this._moveState.back}_updateRotationVector(){this._rotationVector.x=-this._moveState.pitchDown+this._moveState.pitchUp,this._rotationVector.y=-this._moveState.yawRight+this._moveState.yawLeft,this._rotationVector.z=-this._moveState.rollRight+this._moveState.rollLeft}_getContainerDimensions(){return this.domElement!=document?{size:[this.domElement.offsetWidth,this.domElement.offsetHeight],offset:[this.domElement.offsetLeft,this.domElement.offsetTop]}:{size:[window.innerWidth,window.innerHeight],offset:[0,0]}}}function dx(i){if(!(i.altKey||this.enabled===!1)){switch(i.code){case"ShiftLeft":case"ShiftRight":this.movementSpeedMultiplier=.1;break;case"KeyW":this._moveState.forward=1;break;case"KeyS":this._moveState.back=1;break;case"KeyA":this._moveState.left=1;break;case"KeyD":this._moveState.right=1;break;case"KeyR":this._moveState.up=1;break;case"KeyF":this._moveState.down=1;break;case"ArrowUp":this._moveState.pitchUp=1;break;case"ArrowDown":this._moveState.pitchDown=1;break;case"ArrowLeft":this._moveState.yawLeft=1;break;case"ArrowRight":this._moveState.yawRight=1;break;case"KeyQ":this._moveState.rollLeft=1;break;case"KeyE":this._moveState.rollRight=1;break}this._updateMovementVector(),this._updateRotationVector()}}function fx(i){if(this.enabled!==!1){switch(i.code){case"ShiftLeft":case"ShiftRight":this.movementSpeedMultiplier=1;break;case"KeyW":this._moveState.forward=0;break;case"KeyS":this._moveState.back=0;break;case"KeyA":this._moveState.left=0;break;case"KeyD":this._moveState.right=0;break;case"KeyR":this._moveState.up=0;break;case"KeyF":this._moveState.down=0;break;case"ArrowUp":this._moveState.pitchUp=0;break;case"ArrowDown":this._moveState.pitchDown=0;break;case"ArrowLeft":this._moveState.yawLeft=0;break;case"ArrowRight":this._moveState.yawRight=0;break;case"KeyQ":this._moveState.rollLeft=0;break;case"KeyE":this._moveState.rollRight=0;break}this._updateMovementVector(),this._updateRotationVector()}}function px(i){if(this.enabled!==!1)if(this.dragToLook)this._status++;else{switch(i.button){case 0:this._moveState.forward=1;break;case 2:this._moveState.back=1;break}this._updateMovementVector()}}function mx(i){if(this.enabled!==!1&&(!this.dragToLook||this._status>0)){const e=this._getContainerDimensions(),t=e.size[0]/2,n=e.size[1]/2;this._moveState.yawLeft=-(i.pageX-e.offset[0]-t)/t,this._moveState.pitchDown=(i.pageY-e.offset[1]-n)/n,this._updateRotationVector()}}function gx(i){if(this.enabled!==!1){if(this.dragToLook)this._status--,this._moveState.yawLeft=this._moveState.pitchDown=0;else{switch(i.button){case 0:this._moveState.forward=0;break;case 2:this._moveState.back=0;break}this._updateMovementVector()}this._updateRotationVector()}}function _x(){this.enabled!==!1&&(this.dragToLook?(this._status=0,this._moveState.yawLeft=this._moveState.pitchDown=0):(this._moveState.forward=0,this._moveState.back=0,this._updateMovementVector()),this._updateRotationVector())}function vx(i){this.enabled!==!1&&i.preventDefault()}const $h={type:"change"},jl={type:"start"},Md={type:"end"},Gr=new Ma,Xh=new ui,xx=Math.cos(70*Df.DEG2RAD),kt=new P,nn=2*Math.PI,mt={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6},fo=1e-6;class yx extends nd{constructor(e,t=null){super(e,t),this.state=mt.NONE,this.target=new P,this.cursor=new P,this.minDistance=0,this.maxDistance=1/0,this.minZoom=0,this.maxZoom=1/0,this.minTargetRadius=0,this.maxTargetRadius=1/0,this.minPolarAngle=0,this.maxPolarAngle=Math.PI,this.minAzimuthAngle=-1/0,this.maxAzimuthAngle=1/0,this.enableDamping=!1,this.dampingFactor=.05,this.enableZoom=!0,this.zoomSpeed=1,this.enableRotate=!0,this.rotateSpeed=1,this.keyRotateSpeed=1,this.enablePan=!0,this.panSpeed=1,this.screenSpacePanning=!0,this.keyPanSpeed=7,this.zoomToCursor=!1,this.autoRotate=!1,this.autoRotateSpeed=2,this.keys={LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"},this.mouseButtons={LEFT:ps.ROTATE,MIDDLE:ps.DOLLY,RIGHT:ps.PAN},this.touches={ONE:us.ROTATE,TWO:us.DOLLY_PAN},this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this._cursorStyle="auto",this._domElementKeyEvents=null,this._lastPosition=new P,this._lastQuaternion=new Sn,this._lastTargetPosition=new P,this._quat=new Sn().setFromUnitVectors(e.up,new P(0,1,0)),this._quatInverse=this._quat.clone().invert(),this._spherical=new Qc,this._sphericalDelta=new Qc,this._scale=1,this._panOffset=new P,this._rotateStart=new Fe,this._rotateEnd=new Fe,this._rotateDelta=new Fe,this._panStart=new Fe,this._panEnd=new Fe,this._panDelta=new Fe,this._dollyStart=new Fe,this._dollyEnd=new Fe,this._dollyDelta=new Fe,this._dollyDirection=new P,this._mouse=new Fe,this._performCursorZoom=!1,this._pointers=[],this._pointerPositions={},this._controlActive=!1,this._onPointerMove=Mx.bind(this),this._onPointerDown=bx.bind(this),this._onPointerUp=Sx.bind(this),this._onContextMenu=Px.bind(this),this._onMouseWheel=Tx.bind(this),this._onKeyDown=Ax.bind(this),this._onTouchStart=Rx.bind(this),this._onTouchMove=Cx.bind(this),this._onMouseDown=Ex.bind(this),this._onMouseMove=wx.bind(this),this._interceptControlDown=Lx.bind(this),this._interceptControlUp=Dx.bind(this),this.domElement!==null&&this.connect(this.domElement),this.update()}set cursorStyle(e){this._cursorStyle=e,e==="grab"?this.domElement.style.cursor="grab":this.domElement.style.cursor="auto"}get cursorStyle(){return this._cursorStyle}connect(e){super.connect(e),this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointercancel",this._onPointerUp),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.addEventListener("wheel",this._onMouseWheel,{passive:!1}),this.domElement.getRootNode().addEventListener("keydown",this._interceptControlDown,{passive:!0,capture:!0}),this.domElement.style.touchAction="none"}disconnect(){this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerUp),this.domElement.removeEventListener("wheel",this._onMouseWheel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.stopListenToKeyEvents(),this.domElement.getRootNode().removeEventListener("keydown",this._interceptControlDown,{capture:!0}),this.domElement.style.touchAction=""}dispose(){this.disconnect()}getPolarAngle(){return this._spherical.phi}getAzimuthalAngle(){return this._spherical.theta}getDistance(){return this.object.position.distanceTo(this.target)}listenToKeyEvents(e){e.addEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=e}stopListenToKeyEvents(){this._domElementKeyEvents!==null&&(this._domElementKeyEvents.removeEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=null)}saveState(){this.target0.copy(this.target),this.position0.copy(this.object.position),this.zoom0=this.object.zoom}reset(){this.target.copy(this.target0),this.object.position.copy(this.position0),this.object.zoom=this.zoom0,this.object.updateProjectionMatrix(),this.dispatchEvent($h),this.update(),this.state=mt.NONE}pan(e,t){this._pan(e,t),this.update()}dollyIn(e){this._dollyIn(e),this.update()}dollyOut(e){this._dollyOut(e),this.update()}rotateLeft(e){this._rotateLeft(e),this.update()}rotateUp(e){this._rotateUp(e),this.update()}update(e=null){const t=this.object.position;kt.copy(t).sub(this.target),kt.applyQuaternion(this._quat),this._spherical.setFromVector3(kt),this.autoRotate&&this.state===mt.NONE&&this._rotateLeft(this._getAutoRotationAngle(e)),this.enableDamping?(this._spherical.theta+=this._sphericalDelta.theta*this.dampingFactor,this._spherical.phi+=this._sphericalDelta.phi*this.dampingFactor):(this._spherical.theta+=this._sphericalDelta.theta,this._spherical.phi+=this._sphericalDelta.phi);let n=this.minAzimuthAngle,s=this.maxAzimuthAngle;isFinite(n)&&isFinite(s)&&(n<-Math.PI?n+=nn:n>Math.PI&&(n-=nn),s<-Math.PI?s+=nn:s>Math.PI&&(s-=nn),n<=s?this._spherical.theta=Math.max(n,Math.min(s,this._spherical.theta)):this._spherical.theta=this._spherical.theta>(n+s)/2?Math.max(n,this._spherical.theta):Math.min(s,this._spherical.theta)),this._spherical.phi=Math.max(this.minPolarAngle,Math.min(this.maxPolarAngle,this._spherical.phi)),this._spherical.makeSafe(),this.enableDamping===!0?this.target.addScaledVector(this._panOffset,this.dampingFactor):this.target.add(this._panOffset),this.target.sub(this.cursor),this.target.clampLength(this.minTargetRadius,this.maxTargetRadius),this.target.add(this.cursor);let r=!1;if(this.zoomToCursor&&this._performCursorZoom||this.object.isOrthographicCamera)this._spherical.radius=this._clampDistance(this._spherical.radius);else{const a=this._spherical.radius;this._spherical.radius=this._clampDistance(this._spherical.radius*this._scale),r=a!=this._spherical.radius}if(kt.setFromSpherical(this._spherical),kt.applyQuaternion(this._quatInverse),t.copy(this.target).add(kt),this.object.lookAt(this.target),this.enableDamping===!0?(this._sphericalDelta.theta*=1-this.dampingFactor,this._sphericalDelta.phi*=1-this.dampingFactor,this._panOffset.multiplyScalar(1-this.dampingFactor)):(this._sphericalDelta.set(0,0,0),this._panOffset.set(0,0,0)),this.zoomToCursor&&this._performCursorZoom){let a=null;if(this.object.isPerspectiveCamera){const o=kt.length();a=this._clampDistance(o*this._scale);const l=o-a;this.object.position.addScaledVector(this._dollyDirection,l),this.object.updateMatrixWorld(),r=!!l}else if(this.object.isOrthographicCamera){const o=new P(this._mouse.x,this._mouse.y,0);o.unproject(this.object);const l=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),this.object.updateProjectionMatrix(),r=l!==this.object.zoom;const c=new P(this._mouse.x,this._mouse.y,0);c.unproject(this.object),this.object.position.sub(c).add(o),this.object.updateMatrixWorld(),a=kt.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),this.zoomToCursor=!1;a!==null&&(this.screenSpacePanning?this.target.set(0,0,-1).transformDirection(this.object.matrix).multiplyScalar(a).add(this.object.position):(Gr.origin.copy(this.object.position),Gr.direction.set(0,0,-1).transformDirection(this.object.matrix),Math.abs(this.object.up.dot(Gr.direction))<xx?this.object.lookAt(this.target):(Xh.setFromNormalAndCoplanarPoint(this.object.up,this.target),Gr.intersectPlane(Xh,this.target))))}else if(this.object.isOrthographicCamera){const a=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),a!==this.object.zoom&&(this.object.updateProjectionMatrix(),r=!0)}return this._scale=1,this._performCursorZoom=!1,r||this._lastPosition.distanceToSquared(this.object.position)>fo||8*(1-this._lastQuaternion.dot(this.object.quaternion))>fo||this._lastTargetPosition.distanceToSquared(this.target)>fo?(this.dispatchEvent($h),this._lastPosition.copy(this.object.position),this._lastQuaternion.copy(this.object.quaternion),this._lastTargetPosition.copy(this.target),!0):!1}_getAutoRotationAngle(e){return e!==null?nn/60*this.autoRotateSpeed*e:nn/60/60*this.autoRotateSpeed}_getZoomScale(e){const t=Math.abs(e*.01);return Math.pow(.95,this.zoomSpeed*t)}_rotateLeft(e){this._sphericalDelta.theta-=e}_rotateUp(e){this._sphericalDelta.phi-=e}_panLeft(e,t){kt.setFromMatrixColumn(t,0),kt.multiplyScalar(-e),this._panOffset.add(kt)}_panUp(e,t){this.screenSpacePanning===!0?kt.setFromMatrixColumn(t,1):(kt.setFromMatrixColumn(t,0),kt.crossVectors(this.object.up,kt)),kt.multiplyScalar(e),this._panOffset.add(kt)}_pan(e,t){const n=this.domElement;if(this.object.isPerspectiveCamera){const s=this.object.position;kt.copy(s).sub(this.target);let r=kt.length();r*=Math.tan(this.object.fov/2*Math.PI/180),this._panLeft(2*e*r/n.clientHeight,this.object.matrix),this._panUp(2*t*r/n.clientHeight,this.object.matrix)}else this.object.isOrthographicCamera?(this._panLeft(e*(this.object.right-this.object.left)/this.object.zoom/n.clientWidth,this.object.matrix),this._panUp(t*(this.object.top-this.object.bottom)/this.object.zoom/n.clientHeight,this.object.matrix)):(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),this.enablePan=!1)}_dollyOut(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale/=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_dollyIn(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale*=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_updateZoomParameters(e,t){if(!this.zoomToCursor)return;this._performCursorZoom=!0;const n=this.domElement.getBoundingClientRect(),s=e-n.left,r=t-n.top,a=n.width,o=n.height;this._mouse.x=s/a*2-1,this._mouse.y=-(r/o)*2+1,this._dollyDirection.set(this._mouse.x,this._mouse.y,1).unproject(this.object).sub(this.object.position).normalize()}_clampDistance(e){return Math.max(this.minDistance,Math.min(this.maxDistance,e))}_handleMouseDownRotate(e){this._rotateStart.set(e.clientX,e.clientY)}_handleMouseDownDolly(e){this._updateZoomParameters(e.clientX,e.clientX),this._dollyStart.set(e.clientX,e.clientY)}_handleMouseDownPan(e){this._panStart.set(e.clientX,e.clientY)}_handleMouseMoveRotate(e){this._rotateEnd.set(e.clientX,e.clientY),this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(nn*this._rotateDelta.x/t.clientHeight),this._rotateUp(nn*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd),this.update()}_handleMouseMoveDolly(e){this._dollyEnd.set(e.clientX,e.clientY),this._dollyDelta.subVectors(this._dollyEnd,this._dollyStart),this._dollyDelta.y>0?this._dollyOut(this._getZoomScale(this._dollyDelta.y)):this._dollyDelta.y<0&&this._dollyIn(this._getZoomScale(this._dollyDelta.y)),this._dollyStart.copy(this._dollyEnd),this.update()}_handleMouseMovePan(e){this._panEnd.set(e.clientX,e.clientY),this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd),this.update()}_handleMouseWheel(e){this._updateZoomParameters(e.clientX,e.clientY),e.deltaY<0?this._dollyIn(this._getZoomScale(e.deltaY)):e.deltaY>0&&this._dollyOut(this._getZoomScale(e.deltaY)),this.update()}_handleKeyDown(e){let t=!1;switch(e.code){case this.keys.UP:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(nn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,this.keyPanSpeed),t=!0;break;case this.keys.BOTTOM:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(-nn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,-this.keyPanSpeed),t=!0;break;case this.keys.LEFT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(nn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(this.keyPanSpeed,0),t=!0;break;case this.keys.RIGHT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(-nn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(-this.keyPanSpeed,0),t=!0;break}t&&(e.preventDefault(),this.update())}_handleTouchStartRotate(e){if(this._pointers.length===1)this._rotateStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),n=.5*(e.pageX+t.x),s=.5*(e.pageY+t.y);this._rotateStart.set(n,s)}}_handleTouchStartPan(e){if(this._pointers.length===1)this._panStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),n=.5*(e.pageX+t.x),s=.5*(e.pageY+t.y);this._panStart.set(n,s)}}_handleTouchStartDolly(e){const t=this._getSecondPointerPosition(e),n=e.pageX-t.x,s=e.pageY-t.y,r=Math.sqrt(n*n+s*s);this._dollyStart.set(0,r)}_handleTouchStartDollyPan(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enablePan&&this._handleTouchStartPan(e)}_handleTouchStartDollyRotate(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enableRotate&&this._handleTouchStartRotate(e)}_handleTouchMoveRotate(e){if(this._pointers.length==1)this._rotateEnd.set(e.pageX,e.pageY);else{const n=this._getSecondPointerPosition(e),s=.5*(e.pageX+n.x),r=.5*(e.pageY+n.y);this._rotateEnd.set(s,r)}this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(nn*this._rotateDelta.x/t.clientHeight),this._rotateUp(nn*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd)}_handleTouchMovePan(e){if(this._pointers.length===1)this._panEnd.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),n=.5*(e.pageX+t.x),s=.5*(e.pageY+t.y);this._panEnd.set(n,s)}this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd)}_handleTouchMoveDolly(e){const t=this._getSecondPointerPosition(e),n=e.pageX-t.x,s=e.pageY-t.y,r=Math.sqrt(n*n+s*s);this._dollyEnd.set(0,r),this._dollyDelta.set(0,Math.pow(this._dollyEnd.y/this._dollyStart.y,this.zoomSpeed)),this._dollyOut(this._dollyDelta.y),this._dollyStart.copy(this._dollyEnd);const a=(e.pageX+t.x)*.5,o=(e.pageY+t.y)*.5;this._updateZoomParameters(a,o)}_handleTouchMoveDollyPan(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enablePan&&this._handleTouchMovePan(e)}_handleTouchMoveDollyRotate(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enableRotate&&this._handleTouchMoveRotate(e)}_addPointer(e){this._pointers.push(e.pointerId)}_removePointer(e){delete this._pointerPositions[e.pointerId];for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId){this._pointers.splice(t,1);return}}_isTrackingPointer(e){for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId)return!0;return!1}_trackPointer(e){let t=this._pointerPositions[e.pointerId];t===void 0&&(t=new Fe,this._pointerPositions[e.pointerId]=t),t.set(e.pageX,e.pageY)}_getSecondPointerPosition(e){const t=e.pointerId===this._pointers[0]?this._pointers[1]:this._pointers[0];return this._pointerPositions[t]}_customWheelEvent(e){const t=e.deltaMode,n={clientX:e.clientX,clientY:e.clientY,deltaY:e.deltaY};switch(t){case 1:n.deltaY*=16;break;case 2:n.deltaY*=100;break}return e.ctrlKey&&!this._controlActive&&(n.deltaY*=10),n}}function bx(i){this.enabled!==!1&&(this._pointers.length===0&&(this.domElement.setPointerCapture(i.pointerId),this.domElement.ownerDocument.addEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.addEventListener("pointerup",this._onPointerUp)),!this._isTrackingPointer(i)&&(this._addPointer(i),i.pointerType==="touch"?this._onTouchStart(i):this._onMouseDown(i),this._cursorStyle==="grab"&&(this.domElement.style.cursor="grabbing")))}function Mx(i){this.enabled!==!1&&(i.pointerType==="touch"?this._onTouchMove(i):this._onMouseMove(i))}function Sx(i){switch(this._removePointer(i),this._pointers.length){case 0:this.domElement.releasePointerCapture(i.pointerId),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.dispatchEvent(Md),this.state=mt.NONE,this._cursorStyle==="grab"&&(this.domElement.style.cursor="grab");break;case 1:const e=this._pointers[0],t=this._pointerPositions[e];this._onTouchStart({pointerId:e,pageX:t.x,pageY:t.y});break}}function Ex(i){let e;switch(i.button){case 0:e=this.mouseButtons.LEFT;break;case 1:e=this.mouseButtons.MIDDLE;break;case 2:e=this.mouseButtons.RIGHT;break;default:e=-1}switch(e){case ps.DOLLY:if(this.enableZoom===!1)return;this._handleMouseDownDolly(i),this.state=mt.DOLLY;break;case ps.ROTATE:if(i.ctrlKey||i.metaKey||i.shiftKey){if(this.enablePan===!1)return;this._handleMouseDownPan(i),this.state=mt.PAN}else{if(this.enableRotate===!1)return;this._handleMouseDownRotate(i),this.state=mt.ROTATE}break;case ps.PAN:if(i.ctrlKey||i.metaKey||i.shiftKey){if(this.enableRotate===!1)return;this._handleMouseDownRotate(i),this.state=mt.ROTATE}else{if(this.enablePan===!1)return;this._handleMouseDownPan(i),this.state=mt.PAN}break;default:this.state=mt.NONE}this.state!==mt.NONE&&this.dispatchEvent(jl)}function wx(i){switch(this.state){case mt.ROTATE:if(this.enableRotate===!1)return;this._handleMouseMoveRotate(i);break;case mt.DOLLY:if(this.enableZoom===!1)return;this._handleMouseMoveDolly(i);break;case mt.PAN:if(this.enablePan===!1)return;this._handleMouseMovePan(i);break}}function Tx(i){this.enabled===!1||this.enableZoom===!1||this.state!==mt.NONE||(i.preventDefault(),this.dispatchEvent(jl),this._handleMouseWheel(this._customWheelEvent(i)),this.dispatchEvent(Md))}function Ax(i){this.enabled!==!1&&this._handleKeyDown(i)}function Rx(i){switch(this._trackPointer(i),this._pointers.length){case 1:switch(this.touches.ONE){case us.ROTATE:if(this.enableRotate===!1)return;this._handleTouchStartRotate(i),this.state=mt.TOUCH_ROTATE;break;case us.PAN:if(this.enablePan===!1)return;this._handleTouchStartPan(i),this.state=mt.TOUCH_PAN;break;default:this.state=mt.NONE}break;case 2:switch(this.touches.TWO){case us.DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchStartDollyPan(i),this.state=mt.TOUCH_DOLLY_PAN;break;case us.DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchStartDollyRotate(i),this.state=mt.TOUCH_DOLLY_ROTATE;break;default:this.state=mt.NONE}break;default:this.state=mt.NONE}this.state!==mt.NONE&&this.dispatchEvent(jl)}function Cx(i){switch(this._trackPointer(i),this.state){case mt.TOUCH_ROTATE:if(this.enableRotate===!1)return;this._handleTouchMoveRotate(i),this.update();break;case mt.TOUCH_PAN:if(this.enablePan===!1)return;this._handleTouchMovePan(i),this.update();break;case mt.TOUCH_DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchMoveDollyPan(i),this.update();break;case mt.TOUCH_DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchMoveDollyRotate(i),this.update();break;default:this.state=mt.NONE}}function Px(i){this.enabled!==!1&&i.preventDefault()}function Lx(i){i.key==="Control"&&(this._controlActive=!0,this.domElement.getRootNode().addEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function Dx(i){i.key==="Control"&&(this._controlActive=!1,this.domElement.getRootNode().removeEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}const qh=Math.PI/4,Ix=1.25;class Nx{constructor(e,t){Q(this,"camera");Q(this,"orbit");Q(this,"fly");Q(this,"flying",!1);Q(this,"home");Q(this,"flight",null);this.camera=new cn(50,1,.1,6e3);const n=e.focus,s=new P((n.min_x+n.max_x+1)/2,0,(n.min_y+n.max_y+1)/2),r=n.max_x-n.min_x+1,a=n.max_y-n.min_y+1,o=Math.hypot(r,a),l=Math.max(12,o/2*Ix/Math.tan(this.camera.fov*Math.PI/360)),c=s.clone().add(new P(0,Math.sin(qh)*l,Math.cos(qh)*l));this.home={position:c,target:s},this.camera.position.copy(c),this.orbit=new yx(this.camera,t),this.orbit.target.copy(s),this.orbit.enableDamping=!0,this.orbit.maxPolarAngle=Math.PI/2-.02,this.orbit.update(),this.fly=new ux(this.camera,t),this.fly.movementSpeed=Math.max(10,l/3),this.fly.rollSpeed=.5,this.fly.dragToLook=!0,this.fly.enabled=!1,window.addEventListener("keydown",h=>{var u;const d=(u=h.target)==null?void 0:u.tagName;d==="INPUT"||d==="TEXTAREA"||((h.key==="f"||h.key==="F")&&this.toggleFly(),(h.key==="Home"||h.key==="h")&&this.reframe())})}get mode(){return this.flying?"fly":"orbit"}toggleFly(){this.flying=!this.flying,this.orbit.enabled=!this.flying,this.fly.enabled=this.flying,document.body.dataset.camera=this.mode}reframe(){this.flying&&this.toggleFly(),this.camera.position.copy(this.home.position),this.orbit.target.copy(this.home.target),this.orbit.update()}flyTo(e,t,n=2){this.flying&&this.toggleFly();const s=new P(e,n/2,t),r=this.camera.position.clone().sub(this.orbit.target),a=Math.min(Math.max(r.length()*.45,10),26);r.setLength(a),this.flight={fromPos:this.camera.position.clone(),toPos:s.clone().add(r),fromTarget:this.orbit.target.clone(),toTarget:s,t:0}}setPose(e){this.flying&&this.toggleFly();const t=this.home.target,n=this.home.position.distanceTo(t);if(e==="home")this.camera.position.copy(this.home.position);else if(e==="top")this.camera.position.set(t.x,n*.85,t.z+.01);else{const s=Math.PI/12;this.camera.position.set(t.x+Math.sin(.6)*Math.cos(s)*n,Math.sin(s)*n,t.z+Math.cos(.6)*Math.cos(s)*n)}this.orbit.target.copy(t),this.orbit.update()}serialize(){return{position:this.camera.position.toArray(),target:this.orbit.target.toArray()}}restore(e){this.camera.position.fromArray(e.position),this.orbit.target.fromArray(e.target),this.orbit.update()}resize(e,t){this.camera.aspect=e/t,this.camera.updateProjectionMatrix()}tick(e){if(this.flight){this.flight.t=Math.min(1,this.flight.t+e/.6);const t=this.flight.t,n=t<.5?2*t*t:1-(-2*t+2)**2/2;this.camera.position.lerpVectors(this.flight.fromPos,this.flight.toPos,n),this.orbit.target.lerpVectors(this.flight.fromTarget,this.flight.toTarget,n),t>=1&&(this.flight=null)}this.flying?this.fly.update(e):this.orbit.update()}}const ds={grass:new ye("#4a9e4d"),grass_alt:new ye("#459548"),road:new ye("#5a5a62"),power_line:new ye("#d9c445"),plant:new ye("#b03a37"),lot:new ye("#3f3f46"),water:new ye("#3d6fb0")},pi={industrial:new ye("#c47f45"),commercial:new ye("#5b8dd9"),residential:new ye("#79c96e")};function Jl(i){const e={h:0,s:0,l:0};return i.getHSL(e),new ye().setHSL(e.h,e.s*.35,e.l*.3)}const Ux=new ye("#b8d4e8"),Sd=new ye("#8f2f2c"),Yh=new ye("#ffd23e"),Ox=new ye("#ffffff"),Zh="#ff3223",Fx="#010203",Kh=64,kx=.22,Bx=new ye("#cfe8ff"),zx=new ye("#5ee07a"),Hx=new ye("#ff5348");class Vx{constructor(){Q(this,"mesh");this.mesh=new Wt(new ur(.16,10,8),new ct,Kh),this.mesh.count=0,this.mesh.frustumCulled=!1}update(e,t){const n=new He,s=Math.min(e.guests.length,Kh);for(let r=0;r<s;r++){const a=e.guests[r],o=a.path[a.progress]??a.path.at(-1),l=a.path[a.progress+1]??o,c=o[0]+(l[0]-o[0])*t+.5,h=o[1]+(l[1]-o[1])*t+.5;n.setPosition(c,kx,h),this.mesh.setMatrixAt(r,n),this.mesh.setColorAt(r,a.returning?a.happy?zx:Hx:Bx)}this.mesh.count=s,this.mesh.instanceMatrix.needsUpdate=!0,this.mesh.instanceColor&&(this.mesh.instanceColor.needsUpdate=!0)}}const jh=1024,po=.34,Gx=.17;class Wx{constructor(){Q(this,"mesh");this.mesh=new Wt(new Tt(po,po,po),new ct({color:"#ffe066"}),jh),this.mesh.count=0,this.mesh.frustumCulled=!1}update(e,t){const n=new He,s=Math.min(e.vehicles.length,jh);for(let r=0;r<s;r++){const a=e.vehicles[r],o=a.path[a.progress],l=a.path[a.progress+1]??o,c=o[0]+(l[0]-o[0])*t+.5,h=o[1]+(l[1]-o[1])*t+.5;n.setPosition(c,Gx,h),this.mesh.setMatrixAt(r,n)}this.mesh.count=s,this.mesh.instanceMatrix.needsUpdate=!0}}function $x(i){let e=i>>>0;return()=>{e=e+1831565813>>>0;let t=e;return t=Math.imul(t^t>>>15,t|1),t^=t+Math.imul(t^t>>>7,t|61),((t^t>>>14)>>>0)/4294967296}}function Xx(i){let e=2166136261;for(let t=0;t<i.length;t++)e^=i.charCodeAt(t),e=Math.imul(e,16777619);return e>>>0}const qx=30*86400,Yx=.35,Zx=new ye("#c03030");function Kx(i){const e=pi[i.zone_style]??pi.residential,t=(i.powered?e:Jl(e)).clone();if(i.last_build_age_s!==null){const n=Math.max(Yx,1-i.last_build_age_s/qx),s={h:0,s:0,l:0};t.getHSL(s),t.setHSL(s.h,s.s*n,s.l)}return i.build_status==="error"&&t.lerp(Zx,.45),t}const Jh=.72,jx=1.2,Jx=.35,Qx=.14;function Ed(i){return Math.max(Jx,Qx*Math.cbrt(Math.max(0,i)))}function wi(i){const e=new Map(i.objects.map(t=>[t.key,t.row_count]));return t=>Ed(e.get(t.object_key)??0)}class ey{constructor(e,t,n=!1){Q(this,"group",new wt);Q(this,"mesh");Q(this,"roof");Q(this,"base");Q(this,"lots");Q(this,"heightOf");Q(this,"progress");Q(this,"replayProgress",null);this.lots=e.lots,this.heightOf=wi(e),this.progress=t||e.lots.length===0?1:0;const s=new Tt(1,1,1);s.translate(0,.5,0);const r=Math.max(1,e.lots.length);this.mesh=new Wt(s,n?new ct:new vs,r),this.roof=new Wt(s.clone(),new vs,r),this.base=new Wt(s.clone(),new vs,r),this.mesh.count=this.roof.count=this.base.count=e.lots.length;const a=new ye;for(const[o,l]of e.lots.entries()){const c=pi[l.zone_style]??pi.residential,h=n?l.powered?c:Jl(c):Kx(l);this.mesh.setColorAt(o,h),this.roof.setColorAt(o,a.copy(h).multiplyScalar(.55)),this.base.setColorAt(o,a.copy(h).multiplyScalar(.4))}for(const o of[this.mesh,this.roof,this.base])o.instanceColor&&(o.instanceColor.needsUpdate=!0);this.group.add(this.mesh,...n?[]:[this.roof,this.base]),n&&(this.roof.count=this.base.count=0),this.apply()}tick(e){return this.progress>=1?!1:(this.progress=Math.min(1,this.progress+e/jx),this.apply(),!0)}setReplayProgress(e){this.replayProgress=e,this.apply()}apply(){const e=new He,t=1-(1-this.progress)**3;for(const[n,s]of this.lots.entries()){const r=this.replayProgress?this.replayProgress[n]??1:t,a=Math.max(.01,this.heightOf(s)*r),o=s.w-(1-Jh),l=s.h-(1-Jh),c=s.x+s.w/2,h=s.y+s.h/2;e.makeScale(o,a,l),e.setPosition(c,0,h),this.mesh.setMatrixAt(n,e),e.makeScale(o+.08,.055,l+.08),e.setPosition(c,a,h),this.roof.setMatrixAt(n,e),e.makeScale(o+.1,Math.min(.12,a),l+.1),e.setPosition(c,0,h),this.base.setMatrixAt(n,e)}for(const n of[this.mesh,this.roof,this.base])n.instanceMatrix.needsUpdate=!0,n.computeBoundingSphere()}}class ty{constructor(e){Q(this,"group",new wt);const t=wi(e),n=e.lots.filter(r=>r.test_status!==null&&r.test_status!=="fail");if(n.length){const r=new Wt(new Wl(1),new ct,n.length),a=new He,o=new ye;for(const[l,c]of n.entries()){const d=c.test_status==="pass"?.15:.28;a.makeRotationY(Math.PI/4),a.scale(new P(d,d,d)),a.setPosition(c.x+c.w/2,t(c)+.55,c.y+c.h/2),r.setMatrixAt(l,a),o.set(c.test_status==="warn"?"#e0a832":"#5ee07a"),r.setColorAt(l,o)}r.frustumCulled=!1,this.group.add(r)}const s=e.lots.filter(r=>r.freshness_status==="warn"||r.freshness_status==="error");if(s.length){const r=new Wt(new Is(.22,.44,8),new ct,s.length),a=new He,o=new ye;for(const[l,c]of s.entries()){const h=c.test_status!==null?.34:0;a.identity(),a.setPosition(c.x+c.w/2+h,t(c)+.5,c.y+c.h/2),r.setMatrixAt(l,a),o.set(c.freshness_status==="error"?"#e03535":"#e0a832"),r.setColorAt(l,o)}r.frustumCulled=!1,this.group.add(r)}}}function ny(i){const e=new wt;for(const t of i.districts){const n=new ht(new un(t.w,t.h),new ct({color:16777215,transparent:!0,opacity:.14,depthWrite:!1}));n.rotateX(-Math.PI/2),n.position.set(t.x+t.w/2,.02,t.y+t.h/2);const s=new Yu(new Ju(n.geometry),new Vl({color:16777215,transparent:!0,opacity:.35}));s.rotation.copy(n.rotation),s.position.copy(n.position);const r=document.createElement("div");r.className="district-label",r.textContent=t.schema;const a=new Yl(r);a.position.set(t.x+1,.5,t.y+.5),e.add(n,s,a)}return e}const mi="__plant__";function iy(i,e=!1){const t=new wt,n=new ht(new Hi(.55,.7,3.2,12),e?new ct({color:Zh}):new vs({color:Sd}));n.position.y=1.6;const s=new ht(new ur(.42,16,12),new ct({color:e?Zh:Yh}));if(s.position.y=3.4,t.add(n,s),!e){const r=new fp(Yh,18,14);r.position.y=3.6,t.add(r)}return t.position.set(i.plant.x+.5,0,i.plant.y+.5),t.traverse(r=>r.userData.key=mi),t}const gi={"data-engineer":{id:"data-engineer",label:"data engineer",blurb:"Did the pipeline run, and what did it cost? Build errors and the streets they ran on.",chipOrder:["build-error","stale","drift"],overlays:["flow"],defaultPanel:"problems",gauges:["sla","budget"],tourStops:["view","lenses","districts","streets","plant","orphans","load","replay","drift","controls"]},"analytics-engineer":{id:"analytics-engineer",label:"analytics engineer",blurb:"Do the models hold up? Failing tests, warnings, and how much of this is documented.",chipOrder:["tests-fail","tests-warn","drift"],overlays:["usage"],defaultPanel:"problems",gauges:["documented","tested"],tourStops:["view","lenses","districts","library","fire","quiet-city","streets","orphans","controls"]},"on-call":{id:"on-call",label:"on-call responder",blurb:"What is broken right now? Fires, late sources, and the weather they cause downstream.",chipOrder:["tests-fail","source-late","build-error"],overlays:["weather"],defaultPanel:"problems",gauges:["sla","tested"],tourStops:["view","lenses","fire","quiet-city","firehouse","weather","wear","replay","orphans","controls"]},"data-lead":{id:"data-lead",label:"data lead",blurb:"Is my city healthy? Standing neglect, what it costs, and how much context we have.",chipOrder:["stale","drift","source-late"],overlays:["flow","usage"],defaultPanel:"library",gauges:["budget","quiet","documented"],tourStops:["view","lenses","districts","library","plant","orphans","load","quiet-city","controls"]}},Qn={id:"none",label:"no lens",blurb:"The city as the document orders it — every finding, nothing emphasised.",chipOrder:[],overlays:[],defaultPanel:"none",gauges:[],tourStops:["view","lenses","districts","streets","no-lineage","plant","orphans","fire","quiet-city","firehouse","library","weather","weather-unknown","load","wear","drift","replay","controls"]},wd=[gi["data-engineer"],gi["analytics-engineer"],gi["on-call"],gi["data-lead"]];function Qh(i){if(i===null)return null;const e=i.trim().toLowerCase();return e===""||e==="none"?Qn:gi[e]??null}function sy(i,e){const t=Qh(i);if(t)return{lens:t,source:"url",firstRun:!1};const n=e.read();if(n===null)return{lens:Qn,source:"none",firstRun:!0};const s=Qh(n);return s?{lens:s,source:"stored",firstRun:!1}:(e.clear(),{lens:Qn,source:"none",firstRun:!0})}const ry=14*86400,Ta=7*86400,eu=[{id:"tests-fail",label:i=>`● ${i} test${i===1?"":"s"} failing`,tone:"fail",matches:i=>i.test_status==="fail"},{id:"build-error",label:i=>`✕ ${i} build error${i===1?"":"s"}`,tone:"fail",matches:i=>i.build_status==="error"},{id:"source-late",label:i=>`▲ ${i} source${i===1?"":"s"} late`,tone:"warn",matches:i=>i.freshness_status==="error"||i.freshness_status==="warn"},{id:"tests-warn",label:i=>`● ${i} test warning${i===1?"":"s"}`,tone:"warn",matches:i=>i.test_status==="warn"},{id:"stale",label:i=>`◐ ${i} not built in 14d+`,tone:"info",matches:i=>i.last_build_age_s!==null&&i.last_build_age_s>ry},{id:"drift",label:i=>`⌂ ${i} changed shape in 7d`,tone:"info",matches:i=>i.schema_drift_age_s!==null&&i.schema_drift_age_s<Ta}];class ay{constructor(e,t){Q(this,"root");Q(this,"cursors",new Map);Q(this,"doc");Q(this,"lens",Qn);this.visit=t,this.root=document.getElementById("health"),this.doc=e,this.render()}setDoc(e){this.doc=e,this.cursors.clear(),this.render()}setLens(e){this.lens=e,this.render()}findings(e){return this.doc.lots.filter(e.matches).map(t=>({key:t.object_key,lot:t})).sort((t,n)=>t.key.localeCompare(n.key))}render(){const e=eu.map(a=>({chip:a,n:this.findings(a).length})).filter(a=>a.n>0),t=a=>{const o=this.lens.chipOrder.indexOf(a);return o===-1?Number.MAX_SAFE_INTEGER:o},n=e.map((a,o)=>({...a,i:o})).sort((a,o)=>t(a.chip.id)-t(o.chip.id)||a.i-o.i),s=new Set(n.filter(a=>this.lens.chipOrder.includes(a.chip.id)).slice(0,2).map(a=>a.chip.id)),r=n.map(a=>`<button class="chip-h ${a.chip.tone}${s.has(a.chip.id)?" lead":""}" data-chip="${a.chip.id}" title="click to visit each">${a.chip.label(a.n)}</button>`);this.root.innerHTML=r.length?r.join(""):'<span class="chip-h ok">✓ no findings</span>';for(const a of this.root.querySelectorAll("[data-chip]"))a.addEventListener("click",()=>this.cycle(a.dataset.chip))}cycle(e){const t=eu.find(r=>r.id===e);if(!t)return;const n=this.findings(t);if(!n.length)return;const s=this.cursors.get(e)??0;this.cursors.set(e,(s+1)%n.length),this.visit(n[s%n.length].key)}}const oy=new ye("#d8d2ee"),ly=new ye("#9a93b8"),cy=new ye("#e8b93e"),tu=new ye("#e07a30");function hy(i){var h;const e=new wt,t=wi(i),n=new Map(i.objects.map(d=>[d.key,d])),s=[],r=[],a=[],o=[],l=[];for(const d of i.lots){const u=n.get(d.object_key);if(!u)continue;const p=t(d),g=u.columns.map(m=>Kl(m.type));if(g.includes("temporal")){const m=new He;m.makeScale(1,1+p*.18,1),m.setPosition(d.x+d.w/2,p+.06,d.y+d.h/2),s.push(m)}if(g.includes("nested")){const m=new He;m.setPosition(d.x+d.w/2+.24,p+.3,d.y+d.h/2-.24),r.push(m)}if(d.schema_drift_age_s!==null&&d.schema_drift_age_s<Ta){const m=new He;m.makeScale(1,p+.9,1),m.setPosition(d.x+d.w/2-.42,(p+.9)/2,d.y+d.h/2-.42),o.push(m);const f=new He;f.makeRotationZ(Math.PI/2),f.setPosition(d.x+d.w/2-.12,p+.86,d.y+d.h/2-.42),l.push(f)}if(((h=u.dbt)==null?void 0:h.tests.some(m=>/^(unique|primary)/i.test(m.name)))??!1){const m=new He;m.setPosition(d.x+d.w/2,.14,d.y+d.h/2+.36),a.push(m)}}const c=(d,u,p)=>{if(!d.length)return;const g=new Wt(u,new vs({color:p}),d.length);d.forEach((x,m)=>g.setMatrixAt(m,x)),g.frustumCulled=!1,e.add(g)};return c(s,new Is(.12,.7,6),oy),c(r,new Hi(.02,.02,.6,4),ly),c(a,new Tt(.2,.28,.05),cy),c(o,new Tt(.06,1,.06),tu),c(l,new Tt(.06,.8,.06),tu),e}const xs="__library__",or="__firehouse__";function Td(i){const e=document.createElement("div");return e.className="district-label",e.textContent=i,new Yl(e)}function Ad(i,e){return i.traverse(t=>{t.userData.key=e}),i}function uy(i){if(!i.library)return null;const{x:e,y:t}=i.library,n=new wt,s=new ct({color:"#e8e2d0"}),r=new ct({color:"#b8b2a0"}),a=new ht(new Tt(1.5,.16,1.1),r);a.position.set(e+.5,.08,t+.5);const o=new ht(new Tt(1.3,.62,.9),s);o.position.set(e+.5,.16+.31,t+.5),n.add(a,o);for(let h=0;h<4;h+=1){const d=new ht(new Hi(.045,.045,.62,6),s);d.position.set(e+.5-.48+h*.32,.16+.31,t+.5+.5),n.add(d)}const l=new ht(new Tt(1.44,.16,1.04),r);l.position.set(e+.5,.16+.62+.08,t+.5),n.add(l);const c=Td("library");return c.position.set(e+.5,1.2,t+.5),n.add(c),Ad(n,xs)}function dy(i){if(!i.firehouse)return null;const{x:e,y:t}=i.firehouse,n=new wt,s=new ct({color:"#b03028"}),r=new ct({color:"#e0d8c8"}),a=new ht(new Tt(1.4,.7,1),s);a.position.set(e+.5,.35,t+.5);const o=new ht(new Tt(.6,.44,.05),r);o.position.set(e+.5,.22,t+.5+.5);const l=new ht(new Tt(.3,1.1,.3),s);l.position.set(e+.5+.45,.55,t+.5-.25),n.add(a,o,l);const c=Td("firehouse");return c.position.set(e+.5,1.4,t+.5),n.add(c),Ad(n,or)}function Ql(i){i.traverse(e=>{var s;e instanceof Yl&&e.element.remove();const t=e;t.geometry&&t.geometry.dispose();const n=Array.isArray(t.material)?t.material:[t.material];for(const r of n){if(!r)continue;(s=r.map)==null||s.dispose(),r.dispose()}})}const nu=["#ff5a1f","#ffa524","#ffd75e"];class fy{constructor(e){Q(this,"group",new wt);Q(this,"flames",[]);Q(this,"smoke",[]);Q(this,"elapsed",0);Q(this,"burningCount",0);Q(this,"heightOf");Q(this,"standing");Q(this,"lots");this.heightOf=wi(e),this.lots=e.lots,this.standing=e.lots.filter(t=>t.test_status==="fail"),this.build(this.standing)}get count(){return this.burningCount}setOverride(e){this.build(e===null?this.standing:this.lots.filter(t=>e.has(t.object_key)))}build(e){Ql(this.group),this.group.clear(),this.flames=[],this.smoke=[],this.burningCount=e.length;for(const t of e)this.ignite(t,this.heightOf(t))}ignite(e,t){const n=(e.x*31+e.y*17)%7;for(let r=0;r<3;r+=1){const a=.16+.05*((n+r)%3),o=new ht(new Is(a,a*2.6,6),new ct({color:nu[r%nu.length],transparent:!0,opacity:.9})),l=(n+r)/3*Math.PI*2;o.position.set(e.x+e.w/2+Math.cos(l)*.14*e.w,t+a*1.3,e.y+e.h/2+Math.sin(l)*.14*e.h),this.group.add(o),this.flames.push({mesh:o,baseY:o.position.y,baseScale:1,phase:n+r*2.1})}const s=new ht(new ur(.14,6,5),new ct({color:"#5a5a60",transparent:!0,opacity:.55}));s.position.set(e.x+e.w/2,t+.75,e.y+e.h/2),this.group.add(s),this.smoke.push({mesh:s,phase:n})}tick(e){var n;this.elapsed+=e;const t=this.elapsed;for(const s of this.flames){const r=1+.22*Math.sin(t*11+s.phase)*Math.sin(t*5.3+s.phase);s.mesh.scale.set(r,1+.3*Math.abs(Math.sin(t*7+s.phase)),r),s.mesh.rotation.y=t*1.5+s.phase}for(const s of this.smoke){const r=(t*.35+s.phase*.13)%1;s.mesh.position.y=(n=s.mesh.userData).baseY??(n.baseY=s.mesh.position.y),s.mesh.position.y=s.mesh.userData.baseY+r*1.2,s.mesh.material.opacity=.55*(1-r);const a=1+r*1.6;s.mesh.scale.set(a,a,a)}}}const mo=3.2,Xs=2.4,py={select:i=>i.test_status==="fail",cab:"#c03028",light:"#ff3030",phaseSalt:0},my={select:i=>i.freshness_status==="warn"||i.freshness_status==="error",cab:"#d8a028",light:"#ffb830",phaseSalt:3};class Rd{constructor(e,t){Q(this,"group",new wt);Q(this,"trucks",[]);Q(this,"elapsed",0);Q(this,"unreachableCount",0);Q(this,"spec");Q(this,"doc");Q(this,"net",null);Q(this,"standing",[]);this.spec=t,this.doc=e,e.firehouse&&(this.net=new bd(e),this.standing=e.lots.filter(t.select),this.build(this.standing))}get count(){return this.trucks.length}get unreachable(){return this.unreachableCount}setOverride(e){this.doc.firehouse&&this.build(e===null?this.standing:this.doc.lots.filter(t=>e.has(t.object_key)))}build(e){const t=this.net;if(!t||!this.doc.firehouse)return;Ql(this.group),this.group.clear(),this.trucks=[],this.unreachableCount=0;const n=this.spec;for(const s of e){const r=[...Array.from({length:s.w},(h,d)=>[[s.x+d,s.y-1],[s.x+d,s.y+s.h]]).flat(),...Array.from({length:s.h},(h,d)=>[[s.x-1,s.y+d],[s.x+s.w,s.y+d]]).flat()].filter(([h,d])=>t.isDrivable(h,d)),a=t.path([this.doc.firehouse.x,this.doc.firehouse.y],r);if(!a){this.unreachableCount+=1;continue}const o=new wt,l=new ht(new Tt(.34,.16,.18),new ct({color:n.cab}));l.position.y=.1;const c=new ht(new Tt(.08,.06,.08),new ct({color:n.light}));c.position.y=.21,o.add(l,c),this.group.add(o),this.trucks.push({group:o,light:c,path:a,phase:(s.x*13+s.y*7+n.phaseSalt)%5})}}tick(e){this.elapsed+=e;for(const t of this.trucks){const n=t.path.length/mo,s=n+Xs+n+Xs,r=(this.elapsed+t.phase)%s;let a;r<n?a=r*mo:r<n+Xs?a=t.path.length-1:r<n+Xs+n?a=t.path.length-1-(r-n-Xs)*mo:a=0;const o=Math.min(Math.max(Math.floor(a),0),t.path.length-1),l=Math.min(o+1,t.path.length-1),c=a-o,[h,d]=t.path[o],[u,p]=t.path[l];t.group.position.set(h+.5+(u-h)*c,.02,d+.5+(p-d)*c);const g=a>.5;t.light.material.color.set(g&&Math.floor(this.elapsed*6)%2===0?"#ffffff":this.spec.light)}}}class gy extends Rd{constructor(e){super(e,py)}}class _y extends Rd{constructor(e){super(e,my)}}const go=.72,vy="#b3945f",xy="#23231f";class yy{constructor(e){Q(this,"group",new wt);Q(this,"worn",0);const t=wi(e),n=[],s=[];for(const r of e.lots){const a=r.freshness_status;if(a!=="warn"&&a!=="error")continue;this.worn+=1;const o=t(r),l=r.x+r.w/2,c=r.y+r.h-(1-go)/2+.012,h=r.w-(1-go),d=a==="error"?4:2;for(let u=0;u<d;u++){const p=r.x*31+r.y*17+u*13,g=l+(p%7/7-.5)*(h-.2),x=.15+p*3%11/11*Math.max(.2,o-.35);n.push({x:g,y:x,z:c,w:.16+p%3*.04})}a==="error"&&s.push({x:l,z:r.y+r.h/2,w:h+.14,d:r.h-(1-go)+.14})}if(n.length){const r=new Wt(new Tt(1,.12,.03),new ct({color:vy}),n.length),a=new He;for(const[o,l]of n.entries())a.makeScale(l.w,1,1),a.setPosition(l.x,l.y,l.z),r.setMatrixAt(o,a);r.frustumCulled=!1,this.group.add(r)}if(s.length){const r=new Wt(new Tt(1,.1,1),new ct({color:xy,transparent:!0,opacity:.8}),s.length),a=new He;for(const[o,l]of s.entries())a.makeScale(l.w,1,l.d),a.setPosition(l.x,.05,l.z),r.setMatrixAt(o,a);r.frustumCulled=!1,this.group.add(r)}}get count(){return this.worn}}const by={numeric:"#6fa8ff",text:"#79e08a",temporal:"#ffcb52",boolean:"#c9c9d6",nested:"#c07ee8",other:"#9aa0b0"},My="#ff3b30",hi=3,Cd=.72,Sy=.1,er=(Cd-2*Sy-2*.05)/hi,wl=.15,_o=.27,iu=.028;function Pd(i,e,t){const n=Math.max(1,Math.floor((t-.3)/_o)),s=e.slice(0,n*hi),r=Math.ceil(s.length/hi),a=Math.max(.22,(t-r*_o)/2);return s.map((o,l)=>{const c=r-1-Math.floor(l/hi),h=l%hi,d=Math.min(hi,s.length-Math.floor(l/hi)*hi),u=d*er+(d-1)*.05;return{x:i.x+i.w/2-u/2+er/2+h*(er+.05),y:a+c*_o+wl/2,z:i.y+i.h-(1-Cd)/2,column:o}})}function Ey(i){const e=new Map(i.objects.map(c=>[c.key,c.columns])),t=wi(i),n=[];for(const c of i.lots)for(const h of Pd(c,e.get(c.object_key)??[],t(c))){const{column:d}=h;n.push({x:h.x,y:h.y,z:h.z,color:d.test_status==="fail"?My:by[Kl(d.type)],dim:d.description===null&&d.test_status!=="fail"})}if(!n.length)return null;const s=new wt,r=new Wt(new un(er+iu*2,wl+iu*2),new ct({color:"#14101f",side:pn}),n.length),a=new Wt(new un(er,wl),new ct({side:pn}),n.length),o=new He,l=new ye;for(const[c,h]of n.entries())o.identity(),o.setPosition(h.x,h.y,h.z+.004),r.setMatrixAt(c,o),o.setPosition(h.x,h.y,h.z+.008),a.setMatrixAt(c,o),l.set(h.color),h.dim&&l.multiplyScalar(.22),a.setColorAt(c,l);return r.frustumCulled=a.frustumCulled=!1,s.add(r,a),s}const bi=1,Ps=2,Mi=4,Si=8,Tl=[{bit:bi,dx:0,dy:-1},{bit:Ps,dx:1,dy:0},{bit:Mi,dx:0,dy:1},{bit:Si,dx:-1,dy:0}];function Ld(i){const{width:e,height:t}=i.grid,n=Us(i.grid.tiles_rle,e,t),s=i.grid.tile_kinds.indexOf("road"),r=(o,l)=>o>=0&&l>=0&&o<e&&l<t&&n[l*e+o]===s,a=new Uint8Array(e*t);for(let o=0;o<t;o++)for(let l=0;l<e;l++){if(!r(l,o))continue;let c=0;for(const{bit:h,dx:d,dy:u}of Tl)r(l+d,o+u)&&(c|=h);a[o*e+l]=c}return{width:e,height:t,masks:a,isRoad:r,maskAt:(o,l)=>r(o,l)?a[l*e+o]:0}}const wy=.045,su=.13,Ty="#a3a5ad",Ay=.008,Ry=.055,qs=.55,Cy="#b2b0ae",Py="#e0d8c8",Wr=.26,$r=.3,Xr=.06,qr=.09,ru=.026,Ly="#4e4a46",Dy="#d9d2b8",Iy="#9a938a",Ny=.13,as=.22,au=.25,ou=.09,Uy=.03,Oy="#c2bfb4",Fy={s:0,e:Math.PI/2,n:Math.PI,w:-Math.PI/2},ky={n:bi,e:Ps,s:Mi,w:Si},By={n:[0,-1],e:[1,0],s:[0,1],w:[-1,0]};function zy(i,e){const t=[-.5,0,-.5],n=[.5,0,-.5],s=[.5,0,.5],r=[-.5,0,.5],a=[-.5,i,-.5],o=[.5,i,-.5],l=[.5,e,.5],c=[-.5,e,.5],h=(p,g,x,m)=>[...p,...g,...x,...p,...x,...m],d=[...h(a,o,l,c),...h(r,s,n,t),...h(c,l,s,r),...h(t,n,o,a),...h(o,n,s,l),...h(a,c,r,t)],u=new jt;return u.setAttribute("position",new St(d,3)),u.computeVertexNormals(),u}function os(){return new Tt(1,1,1).translate(0,.5,0)}const Hy=new P(0,1,0);function Pn(i,e,t,n,s,r,a=0){return new He().compose(new P(i,e,t),new Sn().setFromAxisAngle(Hy,a),new P(n,s,r))}function Li(i,e,t){const n=new Wt(i,new vs({color:e}),t.length);for(const[s,r]of t.entries())n.setMatrixAt(s,r);return n.frustumCulled=!1,n}class Vy{constructor(e){Q(this,"group",new wt);Q(this,"curbMesh",null);Q(this,"primaries",[]);const t=Ld(e),n=this.curbCuts(e),s=[];for(let r=0;r<t.height;r++)for(let a=0;a<t.width;a++){if(!t.isRoad(a,r))continue;const o=t.masks[r*t.width+a];for(const{bit:l,dx:c,dy:h}of Tl){if(o&l)continue;const d=n.get(`${a},${r},${l}`);if(d==="pave")continue;const u=a+.5+c*.5,p=r+.5+h*.5,g=d==="notch"?[[-.775/2,(1-qs)/2],[(qs+(1-qs)/2)/2,(1-qs)/2]]:[[0,1]];for(const[x,m]of g){const f=c===0?m:su,M=c===0?su:m,E=c===0?x:0,y=c===0?0:x;s.push(Pn(u+E,0,p+y,f,wy,M))}}}s.length&&(this.curbMesh=Li(os(),Ty,s),this.group.add(this.curbMesh)),this.dress(e)}get curbCount(){var e;return(e=this.curbMesh)!=null&&e.parent?this.curbMesh.count:0}get featureCount(){return this.primaries.reduce((e,t)=>e+(t.parent?t.count:0),0)}curbCuts(e){const t=new Map;for(const n of e.street_features){const s=n.kind==="dock"||n.kind==="plaza",r=s?Tl.map(a=>a.bit):n.kind==="apron"?[ky[n.facing??""]??0]:[];for(let a=0;a<n.h;a++)for(let o=0;o<n.w;o++)for(const l of r)t.set(`${n.x+o},${n.y+a},${l}`,s?"pave":"notch")}return t}dress(e){const t=[],n=[],s=[],r=[],a=[],o=[];for(const l of e.street_features){const c=l.x+l.w/2,h=l.y+l.h/2;if(l.kind==="apron"){const d=Fy[l.facing??""]??0,u=(l.facing==="e"||l.facing==="w"?l.h:l.w)*qs,p=l.facing==="e"||l.facing==="w"?l.w:l.h;t.push(Pn(c,0,h,u,1,p,d));const g=this.doorFor(e,l);g&&n.push(g)}else if(l.kind==="dock"){s.push(Pn(c,0,h,l.w,ru,l.h));const d=l.facing==="e"||l.facing==="w",u=d?l.w:l.h,p=Math.max(1,Math.floor(u/au)-1);for(let M=1;M<=p;M++){const E=(d?l.x:l.y)+M*au,y=d?ou:l.w,T=d?l.h:ou,S=d?E:c,R=d?h:E;r.push(Pn(S,ru,R,y,.006,T))}const g=l.facing==="e"?l.x+l.w-as/2:l.facing==="w"?l.x+as/2:c,x=l.facing==="s"?l.y+l.h-as/2:l.facing==="n"?l.y+as/2:h,m=d?as:l.w,f=d?l.h:as;l.facing&&a.push(Pn(g,0,x,m,Ny,f))}else l.kind==="plaza"&&o.push(Pn(c,0,h,l.w,Uy,l.h))}t.length&&this.addPrimary(Li(zy(Ay,Ry),Cy,t)),s.length&&this.addPrimary(Li(os(),Ly,s)),o.length&&this.addPrimary(Li(os(),Oy,o)),n.length&&this.group.add(Li(os(),Py,n)),r.length&&this.group.add(Li(os(),Dy,r)),a.length&&this.group.add(Li(os(),Iy,a))}addPrimary(e){this.primaries.push(e),this.group.add(e)}doorFor(e,t){const n=By[t.facing??""];if(!n)return null;const s=t.x+(t.w-1)*Math.max(0,n[0])+n[0],r=t.y+(t.h-1)*Math.max(0,n[1])+n[1],a=e.lots.find(p=>s>=p.x&&s<p.x+p.w&&r>=p.y&&r<p.y+p.h);if(!a)return null;const o=a.x+qr,l=a.x+a.w-qr,c=a.y+qr,h=a.y+a.h-qr,d=t.x+t.w/2,u=t.y+t.h/2;switch(t.facing){case"e":return Pn(o,0,u,Xr,$r,Wr);case"w":return Pn(l,0,u,Xr,$r,Wr);case"s":return Pn(d,0,c,Wr,$r,Xr);default:return Pn(d,0,h,Wr,$r,Xr)}}}async function Gy(i){const e=new Image;return e.src=i,await new Promise(t=>e.onload=()=>t()),e}const fs=4096,Ft=16,xa=["grass","grass_alt","road","power_line","plant","__pad__","water"],Wy="#3f3f46",Dd=xa.length,Al=16,$y="#46464c",Xy="#2f2f34",qy="#8a8a92",lu="#d8c86a",Yy="#e4e4dc",cu=new Map([[bi,Mi],[Mi,bi],[Ps,Si],[Si,Ps]]);function Zy(i,e,t){const n=Ft,s=3;t===bi?i.fillRect(e+3,s,n-6,1):t===Mi?i.fillRect(e+3,n-s-1,n-6,1):t===Si?i.fillRect(e+s,3,1,n-6):i.fillRect(e+n-s-1,3,1,n-6)}function hu(i,e,t){const n=Ft,s=Math.floor(n/2);if(t===bi)for(let r=1;r<s;r+=4)i.fillRect(e+s,r,1,2);else if(t===Mi)for(let r=s+1;r<n-1;r+=4)i.fillRect(e+s,r,1,2);else if(t===Si)for(let r=1;r<s;r+=4)i.fillRect(e+r,s,2,1);else for(let r=s+1;r<n-1;r+=4)i.fillRect(e+r,s,2,1)}function Ky(i,e,t){const n=Ft;i.fillStyle=$y,i.fillRect(e,0,n,n);const s={n:!(t&bi),e:!(t&Ps),s:!(t&Mi),w:!(t&Si)};i.fillStyle=Xy,s.n&&i.fillRect(e,1,n,1),s.s&&i.fillRect(e,n-2,n,1),s.w&&i.fillRect(e+1,0,1,n),s.e&&i.fillRect(e+n-2,0,1,n),i.fillStyle=qy,s.n&&i.fillRect(e,0,n,1),s.s&&i.fillRect(e,n-1,n,1),s.w&&i.fillRect(e,0,1,n),s.e&&i.fillRect(e+n-1,0,1,n);const r=[bi,Ps,Mi,Si].filter(o=>t&o),a=r.filter(o=>t&cu.get(o));if(r.length>=3){const o=r.filter(l=>!(t&cu.get(l)));i.fillStyle=Yy;for(const l of o.length?o:r)Zy(i,e,l);i.fillStyle=lu;for(const l of a)hu(i,e,l);return}i.fillStyle=lu;for(const o of r)hu(i,e,o)}function jy(i,e){const t=document.createElement("canvas");t.width=(xa.length+Al)*Ft,t.height=Ft;const n=t.getContext("2d");for(const[r,a]of xa.entries()){if(a==="__pad__"){n.fillStyle=Wy,n.fillRect(r*Ft,0,Ft,Ft);continue}const o=i.theme.sprites[a];if(!o)throw new Error(`theme has no sprite ${a}`);const[l,c,h,d]=o;n.drawImage(e,l,c,h,d,r*Ft,0,Ft,Ft)}for(let r=0;r<Al;r++)Ky(n,(Dd+r)*Ft,r);const s=new Ku(t);return s.colorSpace=Gn,s.magFilter=Mt,s.minFilter=Mt,s.generateMipmaps=!1,s}function Jy(i){const{width:e,height:t}=i.grid,n=Us(i.grid.tiles_rle,e,t),s=new Uint8Array(e*t);for(let a=0;a<t;a++)for(let o=0;o<e;o++)s[(t-1-a)*e+o]=n[a*e+o];const r=new hr(s,e,t,lr);return r.magFilter=Mt,r.minFilter=Mt,r.unpackAlignment=1,r.needsUpdate=!0,r}function Qy(i){const{width:e,height:t,masks:n}=Ld(i),s=new Uint8Array(e*t);for(let a=0;a<t;a++)for(let o=0;o<e;o++)s[(t-1-a)*e+o]=n[a*e+o];const r=new hr(s,e,t,lr);return r.magFilter=Mt,r.minFilter=Mt,r.unpackAlignment=1,r.needsUpdate=!0,r}const eb=`
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`,tb=`
  uniform sampler2D indexMap;
  uniform sampler2D roadMask;
  uniform sampler2D atlas;
  uniform vec2 gridSize;
  uniform float cellCount;
  uniform float roadId;
  uniform float roadBase;
  varying vec2 vUv;
  void main() {
    vec2 tile = vUv * gridSize;
    vec2 tileIndex = floor(tile);
    float id = texture2D(indexMap, (tileIndex + 0.5) / gridSize).r * 255.0;
    // uv v runs opposite world z, and rows were stored bottom-up to match, so
    // world-parity needs the flipped row index.
    float row = gridSize.y - 1.0 - tileIndex.y;
    float parity = mod(tileIndex.x + row, 2.0);
    float cell = id < 0.5 ? parity : id + 1.0;
    // Roads pick their connectivity variant instead of the flat slab: curbs
    // only on edges facing non-road, so adjacent tiles fuse into one street.
    if (abs(id - roadId) < 0.5) {
      float mask = texture2D(roadMask, (tileIndex + 0.5) / gridSize).r * 255.0;
      cell = roadBase + mask;
    }
    vec2 local = clamp(fract(tile), 0.5 / 16.0, 15.5 / 16.0);
    gl_FragColor = texture2D(atlas, vec2((cell + local.x) / cellCount, local.y));
  }
`;function nb(i,e){const t=document.createElement("canvas");t.width=Ft*2,t.height=Ft*2;const n=t.getContext("2d"),s=(a,o,l)=>{const[c,h,d,u]=i.theme.sprites[a];n.drawImage(e,c,h,d,u,o,l,Ft,Ft)};s("grass",0,0),s("grass_alt",Ft,0),s("grass_alt",0,Ft),s("grass",Ft,Ft);const r=new Ku(t);return r.colorSpace=sn,r.wrapS=tr,r.wrapT=tr,r.repeat.set(fs/2,fs/2),r.magFilter=Mt,r.minFilter=$n,r}function ib(i,e){const{width:t,height:n}=i.grid,s=new ht(new un(t,n),new En({uniforms:{indexMap:{value:Jy(i)},roadMask:{value:Qy(i)},atlas:{value:jy(i,e)},gridSize:{value:new Fe(t,n)},cellCount:{value:xa.length+Al},roadId:{value:i.grid.tile_kinds.indexOf("road")},roadBase:{value:Dd}},vertexShader:eb,fragmentShader:tb}));s.rotateX(-Math.PI/2),s.position.set(t/2,0,n/2);const r=Math.floor(t/2),a=Math.floor(n/2),o=nb(i,e),l=((r-fs/2)%2+2)%2,c=((a+fs/2+1)%2+2)%2;o.offset.set(l/2,c/2);const h=new ht(new un(fs,fs),new ct({map:o,depthWrite:!1}));h.rotateX(-Math.PI/2),h.position.set(r,-.02,a),h.renderOrder=-1;const d=new wt;return d.add(s,h),d}const uu=4096;function sb(i){const{width:e,height:t,tile_kinds:n}=i.grid,s=Us(i.grid.tiles_rle,e,t),r=new Uint8Array(e*t*4);for(let h=0;h<t;h++)for(let d=0;d<e;d++){const u=n[s[h*e+d]]??"grass";let p=ds[u]??ds.grass;u==="grass"&&(d+h)%2!==0&&(p=ds.grass_alt);const g=((t-1-h)*e+d)*4,x=p.clone().convertLinearToSRGB();r[g]=Math.round(x.r*255),r[g+1]=Math.round(x.g*255),r[g+2]=Math.round(x.b*255),r[g+3]=255}const a=new hr(r,e,t,gn);a.magFilter=Mt,a.minFilter=$n,a.generateMipmaps=!0,a.colorSpace=sn,a.needsUpdate=!0;const o=new ht(new un(e,t),new ct({map:a}));o.rotateX(-Math.PI/2),o.position.set(e/2,0,t/2);const l=new ht(new un(uu,uu),new ct({color:ds.grass_alt}));l.rotateX(-Math.PI/2),l.position.set(e/2,-.02,t/2);const c=new wt;return c.add(o,l),c}function rb(i,e=!1,t){return!e&&t?ib(i,t):sb(i)}const ab=.5,ob=3600,vo=.1;class lb{constructor(e,t,n=!1){Q(this,"vehicles",[]);Q(this,"routes");Q(this,"override",null);this.rng=t;const s=new Map(e.lots.map(r=>[r.object_key,r]));this.routes=e.edges.filter(r=>s.has(r.src)&&s.has(r.dst)&&r.route.length>0).map(r=>{const o=s.get(r.dst).last_build_age_s,l=n?1:o===null?0:Math.max(0,1-o/ob);return{weight:n?r.rate:l*(.25+.75*r.rate),path:r.route.map(([h,d])=>[h,d])}}).filter(r=>r.weight>0)}setOverride(e){this.override=e===null?null:e.map(t=>({weight:1,path:[...t]})),this.vehicles.length=0}tick(){let e=0;for(const t of this.vehicles)t.progress+=1,t.progress<t.path.length&&(this.vehicles[e++]=t);this.vehicles.length=e;for(const t of this.override??this.routes)this.rng()<t.weight*ab&&this.vehicles.push({path:t.path,progress:0})}}const cb=15;class hb{constructor(e){Q(this,"tickCount",0);Q(this,"byLot",null);this.doc=e}get available(){return this.doc.replay!==null}get active(){return this.byLot!==null}get note(){var e;return((e=this.doc.replay)==null?void 0:e.note)??""}start(){if(!this.doc.replay)return;const e=new Map(this.doc.replay.steps.map(t=>[t.object_key,{start:t.start,end:t.start+t.duration}]));this.byLot=this.doc.lots.map(t=>e.get(t.object_key)??{start:-1,end:-1}),this.tickCount=0}tick(){if(!this.byLot||!this.doc.replay)return null;if(this.tickCount+=1,this.tickCount>this.doc.replay.span_ticks+cb)return this.byLot=null,null;const e=this.tickCount;return this.byLot.map(({start:t,end:n})=>t<0?1:e<t?0:e>=n?1:(e-t)/(n-t))}}async function Id(i,e,t){const{flat:n,settle:s,ambient:r,seedFor:a}=t,o=new wt,l=n?void 0:await Gy(`./${e.theme.spritesheet}?t=${Date.now()}`);o.add(rb(e,n,l)),o.add(ny(e));const c=iy(e,n);o.add(c);const h=new ey(e,s,n);o.add(h.group);const d=new fy(e),u=new gy(e),p=new _y(e),g=new yy(e),x=[];for(const f of[uy(e),dy(e)])f&&(o.add(f),x.push(f));let m=null;if(!n){o.add(d.group),o.add(u.group),o.add(p.group),o.add(g.group),o.add(new ty(e).group),m=new Vy(e),o.add(m.group);const f=Ey(e);f&&o.add(f),o.add(hy(e))}return i.add(o),{group:o,buildings:h,plant:c,traffic:new lb(e,a(0),r),fires:d,trucks:u,vans:p,wear:g,streetscape:m,civicTargets:x,replay:new hb(e),rows:new Map(e.objects.map(f=>[f.key,f.row_count]))}}function ub(i,e,t){i.remove(e.group),Ql(e.group);for(const n of t)n.count=0}async function db(i){const e=i.get("flat")==="1",t=i.get("settle")==="1",n=i.get("guests")==="1",s=i.get("ambient")==="1",r=i.get("seed"),a=await xd("./city.json"),o=document.getElementById("app"),l=new mv({antialias:!e});l.setPixelRatio(e?1:Math.min(2,window.devicePixelRatio)),o.appendChild(l.domElement);const c=new gv;c.domElement.className="labels",o.appendChild(c.domElement);const h=new Xf;if(h.background=e?new ye(Fx):Ux,!e){h.add(new up(14675711,4876869,1.1));const f=new mp(16777215,1.6);f.position.set(1,2.2,1.4),h.add(f)}const d=new Wx;h.add(d.mesh);const u=new Vx;n&&h.add(u.mesh);const p=f=>$x((r?Number(r):Xx(a.database.name))^f),g=await Id(h,a,{flat:e,settle:t,ambient:s,seedFor:p}),x=new cx(a,p(2654435769)),m=new Nx(a,l.domElement);return{renderer:l,labels:c,scene:h,app:o,camera:m,doc:a,city:g,guests:x,vehicleLayer:d,guestLayer:u,seedFor:p}}const fb="modulepreload",pb=function(i,e){return new URL(i,e).href},du={},mb=function(e,t,n){let s=Promise.resolve();if(t&&t.length>0){let a=function(h){return Promise.all(h.map(d=>Promise.resolve(d).then(u=>({status:"fulfilled",value:u}),u=>({status:"rejected",reason:u}))))};const o=document.getElementsByTagName("link"),l=document.querySelector("meta[property=csp-nonce]"),c=(l==null?void 0:l.nonce)||(l==null?void 0:l.getAttribute("nonce"));s=a(t.map(h=>{if(h=pb(h,n),h in du)return;du[h]=!0;const d=h.endsWith(".css"),u=d?'[rel="stylesheet"]':"";if(!!n)for(let x=o.length-1;x>=0;x--){const m=o[x];if(m.href===h&&(!d||m.rel==="stylesheet"))return}else if(document.querySelector(`link[href="${h}"]${u}`))return;const g=document.createElement("link");if(g.rel=d?"stylesheet":fb,d||(g.as="script"),g.crossOrigin="",g.href=h,c&&g.setAttribute("nonce",c),document.head.appendChild(g),d)return new Promise((x,m)=>{g.addEventListener("load",x),g.addEventListener("error",()=>m(new Error(`Unable to preload CSS for ${h}`)))})}))}function r(a){const o=new Event("vite:preloadError",{cancelable:!0});if(o.payload=a,window.dispatchEvent(o),!o.defaultPrevented)throw a}return s.then(a=>{for(const o of a||[])o.status==="rejected"&&r(o.reason);return e().catch(r)})};function gb(i){if(typeof i!="object"||i===null)return null;const e=i.generated_at;if(typeof e!="string")return null;const t=Date.parse(e);return Number.isFinite(t)?t:null}async function _b(i,e){try{const t=await fetch(i);if(!t.ok)return{kind:"fetched",at:e};const n=gb(await t.json());return n===null?{kind:"fetched",at:e}:{kind:"exported",at:n}}catch{return{kind:"fetched",at:e}}}function vb(i){const e=Math.max(0,Math.round(i/1e3));if(e<90)return`${e}s`;const t=Math.round(e/60);if(t<90)return`${t}m`;const n=Math.round(e/3600);if(n<36)return`${n}h`;const s=Math.floor(e/86400);return s===1?"1 day":`${s} days`}function xb(i,e){const t=vb(e-i.at);return i.kind==="exported"?`exported ${t} ago`:`as of ${t} ago`}function yb(i){return i.kind==="exported"?`city.json was exported at ${new Date(i.at).toISOString()} (from meta.json)`:"no export time available: this is when your browser fetched city.json, which is the document's own age only when a server generated it for you"}const bb="#ffd75e",fu=.045;class Mb{constructor(e){Q(this,"group",new wt);Q(this,"doc");Q(this,"selected",null);Q(this,"material",new ct({color:bb,transparent:!0,opacity:.85}));this.doc=e}get count(){return this.group.children.length}setDoc(e){this.doc=e,this.rebuild()}setSelection(e){this.selected=e,this.rebuild()}anchor(e,t,n){var o;const s=((o=this.doc.objects.find(l=>l.key===e.object_key))==null?void 0:o.columns)??[],r=n(e),a=Pd(e,s,r).find(l=>l.column.name===t);return a?new P(a.x,a.y,a.z):new P(e.x+e.w/2,r,e.y+e.h/2)}rebuild(){var n;for(const s of[...this.group.children])this.group.remove(s),(n=s.geometry)==null||n.dispose();if(!this.selected)return;const e=new Map(this.doc.lots.map(s=>[s.object_key,s])),t=wi(this.doc);for(const s of this.doc.edges){if(s.src!==this.selected&&s.dst!==this.selected)continue;const r=e.get(s.src),a=e.get(s.dst);if(!(!r||!a))for(const[o,l]of s.columns){const c=this.anchor(r,o,t),h=this.anchor(a,l,t),d=c.distanceTo(h);if(d<.01)continue;const u=new ht(new Tt(fu,fu,d),this.material);u.position.copy(c).lerp(h,.5),u.lookAt(h),this.group.add(u)}}}}const Sb=new ye("#3fa7ff"),pu=new ye("#ffd75e"),Eb=new ye("#ff5533");function wb(i,e){i<.5?e.copy(Sb).lerp(pu,i*2):e.copy(pu).lerp(Eb,(i-.5)*2)}class Tb{constructor(){Q(this,"id","flow");Q(this,"key","t");Q(this,"group",new wt);Q(this,"visible",!0);Q(this,"tiles",0)}get count(){return this.tiles}build(e){var m,f;for(const M of[...this.group.children]){this.group.remove(M);const E=M;(m=E.geometry)==null||m.dispose(),(f=E.material)==null||f.dispose()}this.tiles=0;const t=new Map,n=new Set;for(const M of e.edges){for(const[E,y]of M.route.slice(1,-1))n.add(`${E},${y}`);if(!(M.daily_load_s===null||M.daily_load_s<=0))for(const[E,y]of M.route.slice(1,-1)){const T=`${E},${y}`;t.set(T,(t.get(T)??0)+M.daily_load_s)}}if(!t.size)return;const{width:s,height:r}=e.grid,a=Us(e.grid.tiles_rle,s,r),o=e.grid.tile_kinds.indexOf("road"),l=(M,E)=>M>=0&&E>=0&&M<s&&E<r&&a[E*s+M]===o&&!n.has(`${M},${E}`),c=[...t.entries()];for(;c.length;){const[M,E]=c.pop(),[y,T]=M.split(",").map(Number);for(const[S,R]of[[y+1,T],[y,T+1]]){const v=`${S},${R}`;l(S,R)&&((t.get(v)??0)>=E||(t.set(v,E),c.push([v,E])))}}const h=Math.max(...t.values()),d=new Wt(new un(1,1),new ct({transparent:!0,opacity:.45,depthWrite:!1}),t.size),u=new He,p=new He().makeRotationX(-Math.PI/2),g=new ye;let x=0;for(const[M,E]of t){const[y,T]=M.split(",").map(Number);u.copy(p).setPosition(y+.5,.045,T+.5),d.setMatrixAt(x,u),wb(E/h,g),d.setColorAt(x,g),x+=1}d.frustumCulled=!1,this.group.add(d),this.tiles=t.size,this.group.visible=this.visible}setVisible(e){this.visible=e,this.group.visible=e}toggle(){this.setVisible(!this.visible)}}const Ab={fog:{color:"#eef4f8",layers:4,opacity:.19},overcast:{color:"#c2c9d0",layers:3,opacity:.12}},Rb=Ed(0)-.01,mu=.05,gu=-2;class Cb{constructor(){Q(this,"id","weather");Q(this,"key","w");Q(this,"group",new wt);Q(this,"visible",!0);Q(this,"layers",[]);Q(this,"elapsed",0);this.group.renderOrder=gu}get meshCount(){let e=0;return this.group.traverse(t=>{t.isMesh&&(e+=1)}),e}get weatheredSchemas(){return[...new Set(this.layers.map(e=>e.mesh.userData.schema))].sort()}build(e){var s,r,a;for(const o of[...this.group.children]){this.group.remove(o);const l=o;(s=l.geometry)==null||s.dispose(),(r=l.material)==null||r.dispose()}this.layers=[],this.elapsed=0;const t=((a=e.weather)==null?void 0:a.cells)??[];if(!t.length)return;const n=new Map(e.districts.map(o=>[o.schema,o]));for(const o of t){const l=Ab[o.condition],c=n.get(o.schema);!l||!c||this.fogDistrict(c,l)}this.group.visible=this.visible}fogDistrict(e,t){const n=Rb-mu;for(let s=0;s<t.layers;s+=1){const r=t.layers===1?0:s/(t.layers-1),a=mu+n*r,o=t.opacity*(1-.35*r),l=new ht(new un(e.w,e.h),new ct({color:t.color,transparent:!0,opacity:o,depthWrite:!1,side:pn}));l.rotateX(-Math.PI/2),l.position.set(e.x+e.w/2,a,e.y+e.h/2),l.renderOrder=gu,l.frustumCulled=!1,l.userData.schema=e.schema,this.group.add(l),this.layers.push({mesh:l,baseY:a,baseOpacity:o,phase:(e.x*.7+e.y*1.3+s*2.1)%6.283})}}tick(e){this.elapsed+=e;const t=this.elapsed;for(const n of this.layers){const s=Math.sin(t*.31+n.phase);n.mesh.material.opacity=n.baseOpacity*(.82+.18*s),n.mesh.position.y=n.baseY+.015*s}}setVisible(e){this.visible=e,this.group.visible=e}toggle(){this.setVisible(!this.visible)}}const Rl=1/7,qn={busyLow:"#7b4fd6",busyHigh:"#ff5edb",unrated:"#9fe8ff",quiet:"#79838f"};function Nd(i){return i==null?"unknown":i.runs_seen===0?"quiet":i.rate_per_day===null?"unrated":i.rate_per_day<Rl?"quiet":"busy"}function Ud(i){const e={busy:0,quiet:0,unrated:0,unknown:0,measured:0,source:null,peakRate:0};for(const t of i.objects){const n=t.usage;e[Nd(n)]+=1,n&&(e.measured+=1,e.source??(e.source=n.source),n.rate_per_day!==null&&(e.peakRate=Math.max(e.peakRate,n.rate_per_day)))}return e}function Pb(i,e){const t=Math.log1p(e)-Math.log1p(Rl);if(t<=0)return 0;const n=(Math.log1p(i)-Math.log1p(Rl))/t;return Math.min(1,Math.max(0,n))}const Lb=.95,_u=.13,vu=.35,Db=1.9,Ib=.3,Nb=.055,Ub=.26,xu=.5,Ob=.09,yu=.1,Fb=new ye(qn.busyLow),kb=new ye(qn.busyHigh);class Bb{constructor(){Q(this,"id","usage");Q(this,"key","u");Q(this,"group",new wt);Q(this,"visible",!0);Q(this,"elapsed",0);Q(this,"breathing",[])}get instanceCount(){if(!this.inScene)return 0;let e=0;return this.group.traverse(t=>{const n=t;n.isInstancedMesh&&(e+=n.count)}),e}keysPainted(e){if(!this.inScene)return[];const t=new Set;return this.group.traverse(n=>{if(n.userData.usageState===e)for(const s of n.userData.usageKeys)t.add(s)}),[...t].sort()}get inScene(){let e=this.group;for(;e;){if(e.isScene)return!0;e=e.parent}return!1}build(e){var o,l;for(const c of[...this.group.children]){this.group.remove(c);const h=c;(o=h.geometry)==null||o.dispose(),(l=h.material)==null||l.dispose()}this.breathing=[],this.elapsed=0;const t=new Map(e.objects.map(c=>[c.key,c.usage])),n={busy:[],quiet:[],unrated:[]};for(const c of e.lots){const h=t.get(c.object_key)??null,d=Nd(h);d!=="unknown"&&n[d].push({lot:c,usage:h})}const s=wi(e),r=c=>s(c)+Lb,a=Ud(e).peakRate;n.busy.length&&this.addBars(n.busy,r,a),n.unrated.length&&this.addRings(n.unrated,r),n.quiet.length&&(this.addCones(n.quiet,r),this.addLids(n.quiet,s)),this.group.visible=this.visible}addBars(e,t,n){const s=new ct({transparent:!0,opacity:.95,depthWrite:!1}),r=new Hi(_u,_u,1,10).translate(0,.5,0),a=new Wt(r,s,e.length),o=new He,l=new ye;for(const[c,{lot:h,usage:d}]of e.entries()){const u=Pb(d.rate_per_day,n);o.makeScale(1,vu+(Db-vu)*u,1),o.setPosition(h.x+h.w/2,t(h),h.y+h.h/2),a.setMatrixAt(c,o),a.setColorAt(c,l.copy(Fb).lerp(kb,u))}this.breathing.push(s),this.adopt(a,"busy",e)}addRings(e,t){const n=new $l(Ib,Nb,6,18).rotateX(-Math.PI/2),s=new Wt(n,new ct({color:qn.unrated}),e.length),r=new He;for(const[a,{lot:o}]of e.entries())r.identity(),r.setPosition(o.x+o.w/2,t(o),o.y+o.h/2),s.setMatrixAt(a,r);this.adopt(s,"unrated",e)}addCones(e,t){const n=new Is(Ub,xu,12).rotateX(Math.PI),s=new Wt(n,new ct({color:qn.quiet}),e.length),r=new He;for(const[a,{lot:o}]of e.entries())r.identity(),r.setPosition(o.x+o.w/2,t(o)+xu/2,o.y+o.h/2),s.setMatrixAt(a,r);this.adopt(s,"quiet",e)}addLids(e,t){const n=new Tt(1,1,1).translate(0,.5,0),s=new Wt(n,new ct({color:qn.quiet}),e.length),r=new He;for(const[a,{lot:o}]of e.entries())r.makeScale(o.w-yu,Ob,o.h-yu),r.setPosition(o.x+o.w/2,t(o)+.06,o.y+o.h/2),s.setMatrixAt(a,r);this.adopt(s,"quiet",e)}adopt(e,t,n){e.frustumCulled=!1,e.userData.usageState=t,e.userData.usageKeys=n.map(s=>s.lot.object_key),e.instanceColor&&(e.instanceColor.needsUpdate=!0),this.group.add(e)}tick(e){this.elapsed+=e;const t=.83+.17*Math.sin(this.elapsed*1.7);for(const n of this.breathing)n.opacity=.95*t}setVisible(e){this.visible=e,this.group.visible=e}toggle(){this.setVisible(!this.visible)}}class zb{constructor(){Q(this,"byId",new Map)}register(e){this.byId.set(e.id,e)}get(e){return this.byId.get(e)}applyLens(e){if(e.id!=="none")for(const t of this.byId.values())t.setVisible(e.overlays.includes(t.id))}handleKey(e){const t=e.toLowerCase();for(const n of this.byId.values())if(n.key.toLowerCase()===t)return n.toggle(),!0;return!1}}const Ys=96,ls=22,xo=42,bu=8,Hb=28;function Vb(i,e,t){return t==="up"?i.edges.filter(n=>n.dst===e).map(n=>n.src):i.edges.filter(n=>n.src===e).map(n=>n.dst)}function Mu(i,e,t,n,s){let r=[e];for(let a=1;a<=s&&r.length;a++){const o=[];for(const l of r)for(const c of Vb(i,l,t))n.has(c)||(n.set(c,t==="up"?-a:a),o.push(c));r=o}}function Gb(i,e){const t=i.lots.find(n=>n.object_key===e);return(t==null?void 0:t.test_status)==="fail"||(t==null?void 0:t.build_status)==="error"?"#e03535":(t==null?void 0:t.test_status)==="warn"||(t==null?void 0:t.freshness_status)==="warn"?"#e0a832":(t==null?void 0:t.freshness_status)==="error"?"#e03535":"#6a60a8"}function Wb(i,e){const t=new Map([[e,0]]);Mu(i,e,"up",t,9),Mu(i,e,"down",t,9);let n=!1;if(t.size>Hb){for(const[g,x]of[...t])Math.abs(x)>2&&t.delete(g);n=!0}if(t.size<2)return"";const s=new Map;for(const[g,x]of[...t].sort((m,f)=>m[0].localeCompare(f[0])))s.set(x,[...s.get(x)??[],g]);const r=[...s.keys()].sort((g,x)=>g-x),a=new Map;for(const[g,x]of r.entries())for(const[m,f]of s.get(x).entries())a.set(f,{key:f,layer:g,row:m});const o=r.length*(Ys+xo)-xo,l=Math.max(...[...s.values()].map(g=>g.length))*(ls+bu),c=g=>g.layer*(Ys+xo),h=g=>g.row*(ls+bu),d=i.edges.filter(g=>a.has(g.src)&&a.has(g.dst)).map(g=>{const x=a.get(g.src),m=a.get(g.dst),f=c(x)+Ys,M=h(x)+ls/2,E=c(m),y=h(m)+ls/2,T=(f+E)/2,S=g.provenance==="view_sql"?' stroke-dasharray="4 3"':"";return`<path d="M${f} ${M} C${T} ${M} ${T} ${y} ${E} ${y}" fill="none" stroke="#8f86c9" stroke-width="1.2"${S}/>`}).join(""),u=[...a.values()].map(g=>{const x=g.key.split(".").pop()??g.key,m=x.length>14?`${x.slice(0,13)}…`:x,f=g.key===e,M=f?"#ffffff":Gb(i,g.key),E=f?"#574c9c":"#2c2358";return`<g data-key="${g.key.replace(/"/g,"&quot;")}" style="cursor:pointer"><rect x="${c(g)}" y="${h(g)}" rx="4" width="${Ys}" height="${ls}" fill="${E}" stroke="${M}" stroke-width="${f?1.6:1.2}"/><text x="${c(g)+Ys/2}" y="${h(g)+ls/2+3.5}" text-anchor="middle" font-size="9.5" fill="#f0f0ff">${m}</text><title>${g.key}</title></g>`}).join("");return`<h3>model graph</h3>${n?'<p class="prov">trimmed to ±2 hops</p>':""}<div class="graph-scroll"><svg viewBox="0 0 ${o} ${l}" width="${o}" height="${l}" xmlns="http://www.w3.org/2000/svg">${d}${u}</svg></div>`}class $b{constructor(e,t,n=()=>""){Q(this,"root");this.doc=e,this.onJump=t,this.extras=n,this.root=document.getElementById("inspector")}setDoc(e){this.doc=e}show(e){var t;if(e===null){this.root.hidden=!0;return}this.root.hidden=!1,this.root.innerHTML=e===mi?this.plantHtml():e===xs?this.libraryHtml():e===or?this.firehouseHtml():this.objectHtml(e),(t=this.root.querySelector(".close"))==null||t.addEventListener("click",()=>this.onJump(""));for(const n of this.root.querySelectorAll("[data-key]"))n.addEventListener("click",()=>this.onJump(n.dataset.key))}libraryHtml(){const e=this.doc.objects,t=e.filter(u=>{var p;return(((p=u.dbt)==null?void 0:p.description)??"").length>0}).length,n=e.flatMap(u=>u.columns),s=n.filter(u=>u.description!==null).length,r=e.filter(u=>{var p;return(((p=u.dbt)==null?void 0:p.tags.length)??0)>0}).length,a=e.filter(u=>{var p;return((p=u.dbt)==null?void 0:p.owner)!=null}).length,o=e.filter(u=>{var p;return(((p=u.dbt)==null?void 0:p.tests.length)??0)>0}).length,l=(u,p)=>p?`${Math.round(100*u/p)}%`:"—",c=wa(this.doc,"documented_buildings"),h=c!==null&&c.state==="unknown",d=(u,p,g)=>h?"unknown":`${u} / ${p}${g?` (${l(u,p)})`:""}`;return`
      <button class="close" title="close">×</button>
      <h2>public library</h2>
      <p class="note">The city's context lives here. Every shelf is a count
      of real documentation — filling these in builds the city.</p>
      <dl>
        <dt>objects described</dt><dd>${d(t,e.length,!0)}</dd>
        <dt>columns documented</dt><dd>${d(s,n.length,!0)}</dd>
        <dt>objects tagged</dt><dd>${d(r,e.length,!1)}</dd>
        <dt>owners assigned</dt><dd>${d(a,e.length,!1)}</dd>
        <dt>objects tested</dt><dd>${d(o,e.length,!1)}</dd>
      </dl>
      ${h?`<p class="note">${$e(c.note)}</p>`:""}
      <p class="note">Descriptions come from the dbt manifest. A semantic
      model (Apache Ossie / OSI) is not connected yet — when it is, its
      relationships and ai_context shelve here too.</p>`}firehouseHtml(){const e=this.doc.lots.filter(r=>r.test_status==="fail"),t=this.doc.lots.filter(r=>r.freshness_status==="warn"||r.freshness_status==="error"),n=t.length?t.map(r=>`<li data-key="${$e(r.object_key)}">${$e(r.object_key)} <span class="prov">${$e(r.freshness_status)}</span></li>`).join(""):'<li class="none">no stale sources</li>',s=e.length?e.map(r=>`<li data-key="${$e(r.object_key)}">${$e(r.object_key)}</li>`).join(""):'<li class="none">no active fires</li>';return`
      <button class="close" title="close">×</button>
      <h2>firehouse</h2>
      <h3>active fires (${e.length})</h3>
      <ul>${s}</ul>
      <h3>repair calls (${t.length})</h3>
      <ul>${n}</ul>
      <p class="note">A fire is a failing test; a repair call is a source
      violating its dbt freshness SLA (the worn, boarded-up buildings).
      Trucks and contractor vans on the street mean a problem is awaiting
      response — they never mean a fix is running.</p>
      <p class="note">AI responder: <b>not connected</b> in the local
      version. When connected, dispatch will run an agent against the
      failing model and prepare a suggested fix for review.</p>`}objectHtml(e){const t=this.doc.objects.find(c=>c.key===e),n=this.doc.lots.find(c=>c.object_key===e);if(!t||!n)return`<button class="close">×</button><h2>${$e(e)}</h2>`;const{upstream:s,downstream:r}=yd(this.doc,e),a=this.doc.theme.labels,o=t.dbt,l=[n.freshness_status!==null?`<dt>freshness</dt><dd class="tests-${n.freshness_status==="pass"?"pass":n.freshness_status==="warn"?"warn":"fail"}">${$e(n.freshness_status)} <span class="prov">dbt SLA</span></dd>`:"",n.last_build_age_s!==null?`<dt>last build</dt><dd>${Xb(n.last_build_age_s)} ago</dd>`:"",n.build_status!==null?`<dt>build</dt><dd>${$e(n.build_status)}</dd>`:"",n.test_status!==null?`<dt>tests</dt><dd class="tests-${$e(n.test_status)}">${$e(n.test_status)}</dd>`:""].join("");return`
      <button class="close" title="close">×</button>
      <h2>${$e(t.name)}</h2>
      <dl>
        <dt>${$e(a.schema??"schema")}</dt><dd>${$e(t.schema)}</dd>
        <dt>kind</dt><dd>${t.kind}</dd>
        <dt>${$e(a.rows??"rows")}</dt><dd>${t.row_count.toLocaleString()}</dd>
        <dt>density</dt><dd>${n.target_density} / 8</dd>
        <dt>powered</dt><dd>${n.powered?"yes":"no — takes no part in lineage"}</dd>
        ${o!=null&&o.materialized?`<dt>materialized</dt><dd>${$e(o.materialized)}</dd>`:""}
        ${o!=null&&o.owner?`<dt>owner</dt><dd>${$e(o.owner)}</dd>`:""}
        ${l}
        ${this.extras(e)}
      </dl>
      ${o!=null&&o.description?`<p class="doc">${$e(o.description)}</p>`:""}
      ${o!=null&&o.tags.length?`<p class="chips">${o.tags.map(c=>`<span class="chip">${$e(c)}</span>`).join("")}</p>`:""}
      ${this.semanticHtml(t.semantic)}
      ${Wb(this.doc,e)}
      ${this.columnsHtml(t.columns)}
      ${this.testsHtml((o==null?void 0:o.tests)??[])}
      ${this.lineageHtml("upstream",s)}
      ${this.lineageHtml("downstream",r)}
      ${this.joinsHtml(e)}
    `}semanticHtml(e){if(!El(this.doc))return"";if(e===null)return`<h3>semantic (OSI)</h3><p class="note">no declared dataset —
        the semantic model does not mention this object</p>`;const t=(r,a)=>a.length?`<dt>${r}</dt><dd>${a.map(o=>$e(o)).join(", ")}</dd>`:"",n=e.unique_keys.map(r=>`<li>${r.map(a=>$e(a)).join(", ")}</li>`).join(""),s=e.instructions!==null||e.synonyms.length>0||e.example_queries.length>0;return`
      <h3>semantic (OSI)</h3>
      <dl>
        <dt>dataset</dt><dd>${$e(e.name)} <span class="prov">declared</span></dd>
        ${t("primary key",e.primary_key)}
      </dl>
      ${n?`<h3>unique keys</h3><ul class="cols">${n}</ul>`:""}
      ${e.instructions?`<p class="doc">${$e(e.instructions)}</p>`:""}
      ${e.synonyms.length?`<p class="chips">${e.synonyms.map(r=>`<span class="chip">${$e(r)}</span>`).join("")}</p>`:""}
      ${e.example_queries.length?`<h3>example queries</h3><ul class="cols">${e.example_queries.map(r=>`<li>${$e(r)}</li>`).join("")}</ul>`:""}
      ${s?"":'<p class="note">declared, not yet annotated — no instructions, synonyms or example queries</p>'}`}joinsHtml(e){const t=vd(this.doc,e);if(!t.length)return El(this.doc)?'<h3>declared joins</h3><ul><li class="none">none declared</li></ul>':"";const n=t.map(({join:s,other:r,side:a})=>{const o=a==="many"?"many → one · this object is the many side":"many → one · this object is the one side",l=s.keys.map(([c,h])=>`${$e(c)} → ${$e(h)}`).join(", ");return`<li><span class="door" data-key="${$e(r)}">${$e(r)}</span><span class="prov">${$e(s.provenance)} (OSI)</span><div class="join-line">${$e(s.name)} · ${o}</div><div class="join-line">on ${l}${s.composite?" <span class='prov'>composite</span>":""}</div><div class="join-line">${this.lineageNote(s)}</div></li>`}).join("");return`<h3>declared joins (${t.length})</h3><ul class="joins">${n}</ul>`}lineageNote(e){if(e.lineage_edge===null)return'<span class="lin dash"></span>no lineage on this pair — declared join only';const[t,n]=e.lineage_edge,s=this.doc.edges.find(a=>a.src===t&&a.dst===n);return s?`<span class="lin${s.provenance==="view_sql"?" dash":""}"></span>also lineage ${$e(t)} → ${$e(n)} <span class="prov">${Sl[s.provenance]}</span>`:`<span class="lin dash"></span>names a lineage edge ${$e(t)} → ${$e(n)} that is not in this document`}columnsHtml(e){if(!e.length)return"";const t=e.map(n=>{const s=n.test_status===null?"":`<span class="tests-${n.test_status==="pass"?"pass":n.test_status==="warn"?"warn":"fail"}">●</span> `,r=n.description?`<div class="col-doc">${$e(n.description)}</div>`:"";return`<li>${s}<b>${$e(n.name)}</b> <span class="prov">${$e(n.type.toLowerCase())}</span>${r}</li>`}).join("");return`<h3>columns (${e.length})</h3><ul class="cols">${t}</ul>`}testsHtml(e){if(!e.length)return"";const t=s=>{if(s===null)return"○";const r=s.toLowerCase();return r==="pass"||r==="success"?"<span class='tests-pass'>●</span>":r==="warn"?"<span class='tests-warn'>●</span>":"<span class='tests-fail'>●</span>"};return`<h3>dbt tests</h3><ul class="tests">${e.map(s=>`<li>${t(s.status)} ${$e(s.name)}${s.column?`<span class="prov">on ${$e(s.column)}</span>`:""}${s.status===null?'<span class="prov">never run</span>':""}</li>`).join("")}</ul>`}lineageHtml(e,t){const n=t.length?t.map(s=>`<li data-key="${$e(s.key)}">${$e(s.key)}<span class="prov">${Sl[s.provenance]}</span></li>`).join(""):"<li class='none'>none</li>";return`<h3>${e}</h3><ul>${n}</ul>`}plantHtml(){const e=this.doc.database,t=e.has_known_edges?"":"<p class='note'>no lineage detected — lineage comes from view SQL, so a tables-only database yields none</p>";return`
      <button class="close" title="close">×</button>
      <h2>${$e(e.name)}</h2>
      <dl>
        <dt>${$e(this.doc.theme.labels.database??"database")}</dt><dd>the power plant</dd>
        <dt>objects</dt><dd>${e.object_count}</dd>
        <dt>total rows</dt><dd>${e.total_rows.toLocaleString()}</dd>
      </dl>
      ${t}
    `}}function $e(i){return i.replace(/[&<>"']/g,e=>`&#${e.charCodeAt(0)};`)}function Xb(i){return i<3600?`${Math.max(1,Math.round(i/60))}m`:i<86400?`${Math.round(i/3600)}h`:`${Math.round(i/86400)}d`}const yo=200;class qb{constructor(e,t){Q(this,"root");this.doc=e,this.onPick=t,this.root=document.getElementById("stats"),document.getElementById("stats-button").addEventListener("click",()=>this.toggle()),window.addEventListener("keydown",n=>{n.key==="Escape"&&!this.root.hidden&&this.hide()}),this.root.addEventListener("click",n=>{n.target===this.root&&this.hide()})}setDoc(e){this.doc=e}toggle(){this.root.hidden?this.show():this.hide()}hide(){this.root.hidden=!0}show(){const e=this.doc.objects,n=e.slice(0,yo).map(r=>`
        <tr data-key="${Yr(r.key)}">
          <td>${Yr(r.schema)}</td>
          <td>${Yr(r.name)}</td>
          <td>${r.kind}</td>
          <td class="num">${r.row_count.toLocaleString()}</td>
        </tr>`).join(""),s=e.length>yo?`<p class="note">showing ${yo} of ${e.length} objects</p>`:"";this.root.innerHTML=`
      <div class="stats-card">
        <button class="close" title="close">×</button>
        <h2>${Yr(this.doc.database.name)} — ${e.length} objects, ${this.doc.database.total_rows.toLocaleString()} rows</h2>
        <table>
          <thead><tr><th>schema</th><th>object</th><th>kind</th><th class="num">rows</th></tr></thead>
          <tbody>${n}</tbody>
        </table>
        ${s}
      </div>`,this.root.hidden=!1,this.root.querySelector(".close").addEventListener("click",()=>this.hide());for(const r of this.root.querySelectorAll("tr[data-key]"))r.addEventListener("click",()=>{this.hide(),this.onPick(r.dataset.key)})}}function Yr(i){return i.replace(/[&<>"']/g,e=>`&#${e.charCodeAt(0)};`)}const Yb=14*86400;function Zb(i){const e=[];for(const t of i.lots){const n=[];let s=0;t.test_status==="fail"&&(n.push('<span class="tests-fail">● tests fail</span>'),s=Math.max(s,4)),t.build_status==="error"&&(n.push('<span class="tests-fail">✕ build error</span>'),s=Math.max(s,4)),t.freshness_status==="error"&&(n.push('<span class="tests-fail">▲ source late</span>'),s=Math.max(s,3)),t.freshness_status==="warn"&&(n.push('<span class="tests-warn">▲ freshness warn</span>'),s=Math.max(s,2)),t.test_status==="warn"&&(n.push('<span class="tests-warn">● test warning</span>'),s=Math.max(s,2)),t.schema_drift_age_s!==null&&t.schema_drift_age_s<Ta&&(n.push(`<span class="prov">⌂ shape changed ${Math.round(t.schema_drift_age_s/86400)}d ago</span>`),s=Math.max(s,1)),t.last_build_age_s!==null&&t.last_build_age_s>Yb&&(n.push(`<span class="prov">◐ ${Math.round(t.last_build_age_s/86400)}d old</span>`),s=Math.max(s,1)),n.length&&e.push(Kb(t,s,n))}return e}function Kb(i,e,t){return{key:i.object_key,schema:i.object_key.includes(".")?i.object_key.split(".")[0]:"",severity:e,badges:t,buildAge:i.last_build_age_s,driftAge:i.schema_drift_age_s,buildError:i.build_status==="error",testFail:i.test_status==="fail",testWarn:i.test_status==="warn",sourceLate:i.freshness_status==="error"||i.freshness_status==="warn"}}const ci=i=>i?0:1,jb=(i,e)=>i===null?e===null?0:1:e===null?-1:e-i,Jb=(i,e)=>i===null?e===null?0:1:e===null?-1:i-e,Js=(i,e)=>e.severity-i.severity||i.key.localeCompare(e.key),Qb={"data-engineer":(i,e)=>ci(i.buildError)-ci(e.buildError)||jb(i.buildAge,e.buildAge)||Js(i,e),"analytics-engineer":(i,e)=>ci(i.testFail)-ci(e.testFail)||ci(i.testWarn)-ci(e.testWarn)||Js(i,e),"on-call":(i,e)=>e.severity-i.severity||ci(i.sourceLate)-ci(e.sourceLate)||Jb(i.buildAge,e.buildAge)||i.key.localeCompare(e.key),"data-lead":(i,e)=>i.schema.localeCompare(e.schema)||Js(i,e),none:Js};class eM{constructor(e,t){Q(this,"root");Q(this,"doc");Q(this,"lens",Qn);this.visit=t,this.doc=e,this.root=document.getElementById("problems"),window.addEventListener("keydown",n=>{var r;const s=(r=n.target)==null?void 0:r.tagName;s==="INPUT"||s==="TEXTAREA"||((n.key==="p"||n.key==="P")&&this.toggle(),n.key==="Escape"&&!this.root.hidden&&this.hide())})}setDoc(e){this.doc=e,this.root.hidden||this.show()}setLens(e){this.lens=e,this.root.hidden||this.show()}toggle(){this.root.hidden?this.show():this.hide()}hide(){this.root.hidden=!0}gauges(){var g;const e=this.doc.objects,t=e.flatMap(x=>x.columns),n=t.filter(x=>x.description!==null).length,s=e.filter(x=>{var m;return(((m=x.dbt)==null?void 0:m.tests.length)??0)>0}).length,r=this.doc.lots.filter(x=>x.freshness_status!==null).length,a=(x,m)=>m?`${Math.round(100*x/m)}%`:"—",o=e.filter(x=>x.usage!==null),l=o.filter(x=>x.usage.runs_seen===0).length,c=this.doc.budget,h=x=>{const m=wa(this.doc,x);return m!==null&&m.state==="unknown"?m.note:null},d=h("documented_buildings"),u=h("tested_buildings"),p=h("sources_under_sla");return[{id:"documented",text:d?"columns documented — unknown":`columns documented ${a(n,t.length)}`,title:d??`${n} of ${t.length} columns carry a description (dbt manifest)`},{id:"tested",text:u?"objects tested — unknown":`objects tested ${a(s,e.length)}`,title:u??`${s} of ${e.length} objects declare at least one dbt test`},{id:"sla",text:p?"freshness SLAs — unknown":`freshness SLAs ${r}`,title:p??"sources dbt judged against a declared freshness SLA"},{id:"budget",text:c?`compute ${c.currency} ${((g=c.daily_cost)==null?void 0:g.toFixed(2))??"—"}/day`:"compute cost unpriced",title:c?`${c.price_source} — ${c.priced_objects} priced, ${c.unpriced_objects} unpriced`:"no run history to price: unknown, not free"},{id:"quiet",text:o.length?`quiet buildings ${l}/${o.length}`:"quiet buildings — (no usage measured)",title:o.length?`${l} of ${o.length} measured objects appeared in zero runs; ${e.length-o.length} objects have no usage measurement at all`:"no object carries a usage measurement — unknown, never unused"}]}coverageHtml(){const e=n=>{const s=this.lens.gauges.indexOf(n);return s===-1?Number.MAX_SAFE_INTEGER:s},t=this.gauges().map((n,s)=>({gauge:n,i:s})).sort((n,s)=>e(n.gauge.id)-e(s.gauge.id)||n.i-s.i);return t.length?'<p class="coverage">'+t.map(({gauge:n})=>`<span data-gauge="${n.id}"${this.lens.gauges.includes(n.id)?' class="lead"':""} title="${n.title.replace(/"/g,"&quot;")}">${n.text}</span>`).join(" · ")+"</p>":""}show(){const e=Zb(this.doc).sort(Qb[this.lens.id]??Js),t=e.length?e.map(n=>`<li data-key="${n.key.replace(/"/g,"&quot;")}"><b>${n.key}</b><span class="badges">${n.badges.join(" ")}</span></li>`).join(""):'<li class="none">✓ nothing needs attention</li>';this.root.innerHTML=`<h3>needs attention (${e.length})</h3>${this.coverageHtml()}<ul>${t}</ul>`,this.root.hidden=!1;for(const n of this.root.querySelectorAll("li[data-key]"))n.addEventListener("click",()=>this.visit(n.dataset.key))}}class tM{constructor(){Q(this,"panel");Q(this,"requests",[]);Q(this,"visible",!1);this.panel=document.createElement("div"),this.panel.id="requests-panel",this.panel.className="hud-panel",this.panel.hidden=!0,document.getElementById("app").appendChild(this.panel)}async load(e){try{const t=await fetch(e);return t.ok?(this.requests=tt(_d).parse(await t.json()),this.render(),!0):!1}catch{return!1}}toggle(){this.visible=!this.visible,this.panel.hidden=!this.visible}render(){const e={CRITICAL:0,HIGH:1,MEDIUM:2,LOW:3},t=[...this.requests].sort((n,s)=>e[n.priority]-e[s.priority]);this.panel.innerHTML=`
      <div class="panel-header">
        <b>Data Requests</b>
        <span class="provenance">SIMULATED</span>
      </div>
      <table>
        ${t.map(n=>`
          <tr>
            <td><span class="badge ${n.priority.toLowerCase()}">${n.priority}</span></td>
            <td>${n.description}</td>
            <td>${n.status}</td>
          </tr>`).join("")}
      </table>
    `}}class nM{constructor(e,t){Q(this,"root");Q(this,"input");Q(this,"list");Q(this,"entries",[]);Q(this,"cursor",0);this.visit=t,this.root=document.getElementById("search"),this.root.innerHTML=`<div class="search-card"><input type="text"
      placeholder="find a table, view, tag, owner…" spellcheck="false" /><ul></ul></div>`,this.input=this.root.querySelector("input"),this.list=this.root.querySelector("ul"),this.index(e),window.addEventListener("keydown",n=>{var a;const s=(a=n.target)==null?void 0:a.tagName;!(s==="INPUT"||s==="TEXTAREA")&&(n.key==="/"||(n.metaKey||n.ctrlKey)&&n.key==="k")&&(n.preventDefault(),this.open())}),this.input.addEventListener("keydown",n=>{n.key==="Escape"&&this.close(),n.key==="ArrowDown"&&(n.preventDefault(),this.move(1)),n.key==="ArrowUp"&&(n.preventDefault(),this.move(-1)),n.key==="Enter"&&this.pick(this.cursor),n.stopPropagation()}),this.input.addEventListener("input",()=>{this.cursor=0,this.render()}),this.root.addEventListener("click",n=>{n.target===this.root&&this.close()})}setDoc(e){this.index(e)}index(e){this.entries=[{key:"__plant__",label:`⚡ ${e.database.name} (the database)`,haystack:`${e.database.name} database plant`.toLowerCase()},...e.library?[{key:"__library__",label:"📚 public library (context & docs)",haystack:"library context documentation docs coverage"}]:[],...e.firehouse?[{key:"__firehouse__",label:"🚒 firehouse (fire response)",haystack:"firehouse fire response dispatch agents failing tests"}]:[],...e.objects.map(t=>{var n,s;return{key:t.key,label:t.key,haystack:[t.key,t.kind,...((n=t.dbt)==null?void 0:n.tags)??[],((s=t.dbt)==null?void 0:s.owner)??""].join(" ").toLowerCase()}})]}matches(){const e=this.input.value.trim().toLowerCase();return e?this.entries.filter(t=>t.haystack.includes(e)).slice(0,12):this.entries.slice(0,12)}open(){this.root.hidden=!1,this.input.value="",this.cursor=0,this.render(),this.input.focus()}close(){this.root.hidden=!0,this.input.blur()}move(e){const t=this.matches().length;t&&(this.cursor=(this.cursor+e+t)%t,this.render())}pick(e){const t=this.matches()[e];t&&(this.close(),this.visit(t.key))}render(){const e=this.matches().map((t,n)=>`<li class="${n===this.cursor?"active":""}" data-i="${n}">${t.label}</li>`).join("");this.list.innerHTML=e||'<li class="none">no matches</li>';for(const t of this.list.querySelectorAll("li[data-i]"))t.addEventListener("click",()=>this.pick(Number(t.dataset.i)))}}function Di(i){return`#${i.clone().convertLinearToSRGB().getHexString()}`}function Su(i){const e=[["table / view",[Di(pi.industrial),Di(pi.commercial),Di(pi.residential)]],["no lineage",[Di(Jl(pi.residential))]],["road (lineage)",[Di(ds.road)]],["power line",[Di(ds.power_line)]],["database",[Di(Sd)]],["tests: fail = ON FIRE / warn / pass",["#ff5a1f","#e0a832","#5ee07a"]],["source late (dbt SLA)",["#e0a832"]],["traffic = built in the last hour",[]],["road heat = compute load (s/day)",["#3fa7ff","#ffd75e","#ff5533"]],["stale source = worn building, contractor van",["#b3945f","#d8a028"]]],t=i==null?void 0:i.weather;if(t){const s=t.cells.filter(r=>r.condition!=="clear").length;e.push(s?[`fog = district fed by a late source (${s})`,["#e4ecf2","#b7bec6"],t.note]:["weather: none to show",[],t.note])}if(i){const s=Ud(i),r=`source: ${s.source??"none"} — build/run appearances, not query traffic; beacon height is cadence relative to this city's busiest object`;s.measured&&(e.push([`usage beacon = runs/day (${s.busy} busy)`,[qn.busyLow,qn.busyHigh],r]),s.quiet&&e.push([`quiet lid = measured, little used (${s.quiet})`,[qn.quiet],r]),s.unrated&&e.push([`usage ring = seen, cadence unknown (${s.unrated})`,[qn.unrated],"fewer than two appearances, or a zero span: no cadence to report"])),s.unknown&&e.push([`usage unmeasured for ${s.unknown} — unknown, not unused`,[],"the run history says nothing about these objects; that is a gap in the history, not a fact about the table"])}const n=document.getElementById("legend");n.innerHTML=e.map(([s,r,a])=>`<div class="legend-row"${a?` title="${a.replace(/"/g,"&quot;")}"`:""}>${r.map(o=>`<span class="swatch" style="background:${o}"></span>`).join("")}<span>${s}</span></div>`).join("")}const bo="tycoon-city.lens",Eu={read(){try{return localStorage.getItem(bo)}catch{return null}},write(i){try{localStorage.setItem(bo,i)}catch{}},clear(){try{localStorage.removeItem(bo)}catch{}}};function sa(i){return i.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;")}function iM(i){return[i.chipOrder.length?`leads with ${i.chipOrder.slice(0,2).join(" + ")}`:"",i.overlays.length?`${i.overlays.join(" + ")} overlay`:"no overlay",i.defaultPanel==="none"?"":`opens the ${i.defaultPanel} panel`].filter(Boolean).join(" · ")}class sM{constructor(e){Q(this,"root");this.onPick=e,this.root=document.getElementById("lens-modal")}open(){const e=wd.map(t=>`<button class="lens-card" data-lens="${t.id}"><b>${sa(t.label)}</b><span class="blurb">${sa(t.blurb)}</span><span class="detail">${sa(iM(t))}</span></button>`).join("");this.root.innerHTML=`<div class="lens-modal-card"><h2>Which job are you here to do?</h2><p class="note">A lens re-weights what this HUD shows you first. It never
       changes a number: every lens counts the same city.</p><div class="lens-cards">${e}</div><button class="lens-skip" data-lens="none">skip — show me everything</button></div>`,this.root.hidden=!1;for(const t of this.root.querySelectorAll("[data-lens]"))t.addEventListener("click",()=>{const n=t.dataset.lens;this.close(),this.onPick(n==="none"?Qn:gi[n],!0)})}close(){this.root.hidden=!0}}class rM{constructor(e){Q(this,"root");this.onPick=e,this.root=document.getElementById("lens-switch"),this.root.innerHTML='<label>lens <select id="lens-select" title="role lens — presentation only">'+[Qn,...wd].map(t=>`<option value="${t.id}">${sa(t.label)}</option>`).join("")+"</select></label>",this.select().addEventListener("change",()=>{const t=this.select().value;this.onPick(t==="none"?Qn:gi[t],!0)})}select(){return this.root.querySelector("select")}setLens(e){this.select().value=e.id}}const aM=(i,e)=>i.lots.map(t=>t.object_key).filter(t=>t.startsWith(`${e}.`)).sort(),wu=(i,e)=>aM(i,e)[0]??null,ec=(i,e)=>i.lots.filter(e).sort((t,n)=>t.object_key.localeCompare(n.object_key))[0]??null,Zr=i=>ec(i,e=>e.test_status==="fail"),Kr=i=>ec(i,e=>e.freshness_status==="warn"||e.freshness_status==="error"),Mo=i=>ec(i,e=>e.schema_drift_age_s!==null&&e.schema_drift_age_s<Ta),So=i=>i.edges.filter(e=>e.route.length>0)[0]??null,Eo=i=>i.edges.filter(e=>e.daily_load_s!==null&&e.daily_load_s>0).sort((e,t)=>t.daily_load_s-e.daily_load_s)[0]??null,jr=i=>{var e;return(((e=i.weather)==null?void 0:e.cells)??[]).filter(t=>t.condition!=="clear")},oM=i=>Math.round(i/86400),lM=[{id:"view",title:"You are looking at a 3D city",requires:()=>!0,body:()=>"This is a three-dimensional city — not a 2D map or a static diagram. Drag to orbit, scroll to zoom, click a building to inspect it. Arrow keys (or WASD) move the camera; press F to fly through it, H to reframe, R to re-read the catalog. Nothing here is a mockup: every building, street, and signal is measured from the real document."},{id:"lenses",title:"Four lenses, one city",requires:()=>!0,body:()=>"Four presets re-weight the SAME city for the job you do: data engineer (build errors and street load), analytics engineer (failing tests and documentation), on-call responder (fires and freshness), and data lead (cost, context, quiet). Switch with the footer picker or ?lens=<name>. A lens never invents numbers — chips, gauges, and overlays just change order and defaults."},{id:"districts",title:"Schemas are districts",requires:i=>i.districts.length>0&&i.lots.length>0,body:i=>`Every schema is its own neighbourhood — ${i.districts.length} here: ${i.districts.map(e=>e.schema).join(", ")}. Each building is a table or a view, and its height is its row count. Nothing on this map is decoration.`,target:i=>wu(i,i.districts[0].schema)},{id:"streets",title:"Roads follow lineage",requires:i=>So(i)!==null,body:i=>{const e=So(i);return`The road network is not a decoration around the graph — it IS the graph. Lineage from the catalog IS the streets: ${i.edges.length} lineage edges are paved here. Each street follows a real data flow from ${e.src} → ${e.dst}. Freight on it means that build really moved data.`},target:i=>So(i).dst},{id:"no-lineage",title:"A city with no streets",requires:i=>!i.database.has_known_edges,body:()=>"No lineage was detected in this catalog, so there are no streets to drive. The buildings still stand — an unconnected city is a finding about the catalog, never a blank map pretending nothing is there."},{id:"plant",title:"The database is the power plant",requires:i=>i.objects.length>0,body:i=>`${i.database.name} is the plant: ${i.database.object_count} objects, ${i.database.total_rows.toLocaleString()} rows. POWER_LINE arterials radiate from it to every lot — a building with no power line is one nothing can read.`,target:()=>mi},{id:"orphans",title:"Dimmed buildings are orphans",requires:i=>i.objects.length>0,body:i=>{const e=i.lots.filter(t=>!i.edges.some(n=>n.src===t.object_key||n.dst===t.object_key)).length;return`${e} building${e===1?" is":"s are"} dimmed here — an orphan: no edge touches it, no power line reaches it, no street leads to it. An unconnected building is a finding about the catalog, not a rendering bug. The strip would tell you if it had tests.`}},{id:"fire",title:"A failing test is a fire",requires:i=>Zr(i)!==null,body:i=>`${Zr(i).object_key} is ON FIRE: its dbt tests failed. Fires are the highest-priority signal on this map — fog is capped below the lowest roof so it can never hide one.`,target:i=>Zr(i).object_key},{id:"quiet-city",title:"A quiet city",requires:i=>Zr(i)===null,body:()=>"No failing tests here — that's what a quiet city looks like. Nothing is burning, and nothing is pretending to: the strip would say so the moment one test failed."},{id:"firehouse",title:"The firehouse dispatches",requires:i=>i.firehouse!==null,body:i=>{const e=i.lots.filter(n=>n.test_status==="fail").length,t=i.lots.filter(n=>n.freshness_status==="warn"||n.freshness_status==="error").length;return`One truck per fire (${e} now), one contractor van per stale source (${t} repair calls). A truck on the street means a problem is AWAITING response — it never means a fix is running. The AI responder is not connected.`},target:()=>or},{id:"library",title:"The library is your context",requires:i=>i.library!==null&&i.objects.length>0,body:i=>{const e=wa(i,"documented_buildings");if(e!==null&&e.state==="unknown")return`Every shelf is a count of real documentation, and these shelves are unknown rather than empty: ${e.note}. Join a dbt manifest and the counts appear — they are artifacts, never points.`;const t=i.objects.flatMap(r=>r.columns),n=t.filter(r=>r.description!==null).length,s=i.objects.filter(r=>{var a;return(((a=r.dbt)==null?void 0:a.tests.length)??0)>0}).length;return`Every shelf is a count of real documentation: ${n}/${t.length} columns described, ${s}/${i.objects.length} objects tested. Writing docs is how you build this city out — the counts are artifacts, never points.`},target:()=>xs},{id:"weather",title:"Fog is source freshness",requires:i=>jr(i).length>0,body:i=>`A late source fogs every district it FEEDS — not its own, which is where the problem actually is. Under weather now: ${jr(i).map(t=>`${t.schema} (${t.condition}, from ${t.worst_source??"?"})`).join(", ")}. W toggles it.`,target:i=>wu(i,jr(i)[0].schema),overlay:"weather"},{id:"weather-unknown",title:"Weather nobody judged",requires:i=>jr(i).length===0,body:i=>{var e;return`No fog on this map, and that is not the same as fine weather: ${((e=i.weather)==null?void 0:e.note)??"this document carries no weather block at all"}. Clear-because-unknown is never drawn as clear-because-good.`}},{id:"load",title:"Road heat is compute load",requires:i=>Eo(i)!==null,body:i=>{const e=Eo(i);return`Heat on a street is measured: build cadence × mean build cost, accumulated per tile, so a shared trunk glows with everything it carries. Hottest here: ${e.src} → ${e.dst} at ${e.daily_load_s.toFixed(1)}s/day. T toggles it.`},target:i=>Eo(i).dst,overlay:"flow"},{id:"wear",title:"Wear and tear, and the contractors",requires:i=>Kr(i)!==null,body:i=>`${Kr(i).object_key} is boarded up: its source missed the freshness SLA dbt declared for it (${Kr(i).freshness_status}). The amber van answering the call is a dispatch, never a repair anyone has made.`,target:i=>Kr(i).object_key},{id:"drift",title:"Cranes mean the shape moved",requires:i=>Mo(i)!==null,body:i=>{const e=Mo(i);return`A crane over a roof means the object's SHAPE changed recently — ${e.object_key}, ${oM(e.schema_drift_age_s)}d ago. Under construction, literally: columns came or went since the last time you looked.`},target:i=>Mo(i).object_key},{id:"replay",title:"Replay a real run",requires:i=>{var e;return(((e=i.replay)==null?void 0:e.steps.length)??0)>0},body:i=>`"Replay a run" steps through one real dbt invocation — ${i.replay.steps.length} steps. ${i.replay.note}. Buildings grow as they build, failures burn, and traffic runs only on the streets that step actually used.`,target:i=>i.replay.steps[0].object_key},{id:"controls",title:"Controls",requires:()=>!0,body:()=>"Navigation: drag to orbit, scroll to zoom, arrow keys (or WASD) to move. Click any building to inspect it. F toggles fly mode, H reframes, R re-reads the catalog in place. T/W/U toggle road-load, weather, and usage overlays. ?tour=1 walks this tour; ?lens=<name> switches role presets."}],Tu="tycoon-city.tour",cM={read:()=>{try{return localStorage.getItem(Tu)}catch{return null}},write:i=>{try{localStorage.setItem(Tu,i)}catch{}}};class hM{constructor(e){Q(this,"root");Q(this,"store");Q(this,"playlist",[]);Q(this,"at",0);this.deps=e,this.root=document.getElementById("tour"),this.store=e.store??cM,window.addEventListener("keydown",t=>{var s;if(this.root.hidden)return;const n=(s=t.target)==null?void 0:s.tagName;n==="INPUT"||n==="TEXTAREA"||(t.key==="Escape"&&this.skip(),(t.key==="Enter"||t.key==="n"||t.key==="N")&&this.next())})}start(e=!1){e&&this.store.write("");const t=this.store.read();if(!e&&t==="done"||(this.playlist=this.stops(),!this.playlist.length))return;const n=e?null:t,s=n?this.playlist.findIndex(r=>r.id===n):0;this.at=s>=0?s:0,this.render()}stops(){const e=lM.filter(n=>!n.requires||n.requires(this.deps.doc())),t=this.deps.lens().tourStops;return t.length?t.map(n=>e.find(s=>s.id===n)).filter(n=>n!==void 0):e}next(){if(this.at+1>=this.playlist.length){this.finish();return}this.at+=1,this.store.write(this.playlist[this.at].id),this.render()}skip(){this.finish()}finish(){this.store.write("done"),this.root.hidden=!0}render(){var s;const e=this.playlist[this.at],t=this.deps.doc();this.store.write(e.id),this.root.hidden=!1,this.root.innerHTML=`<div class="tour-card" data-stop="${e.id}"><h3>${e.title}<span class="tour-progress">${this.at+1} / ${this.playlist.length}</span></h3><p>${e.body(t)}</p><div class="tour-buttons"><button class="tour-next">${this.at+1>=this.playlist.length?"done":"next"}</button><button class="tour-skip">skip</button><span class="keys">enter / n · esc</span></div></div>`,this.root.querySelector(".tour-next").addEventListener("click",()=>this.next()),this.root.querySelector(".tour-skip").addEventListener("click",()=>this.skip()),e.overlay&&this.deps.setOverlay&&this.deps.setOverlay(e.overlay);const n=((s=e.target)==null?void 0:s.call(e,t))??null;n&&this.deps.visit(n)}}const uM="database-tycoon.runs",dM="database-tycoon.run",Od=1,Fd=rt({id:ie(),command:ie(),started_at:ie(),target:ie(),ok:dr(),models_error:we().int().nonnegative(),tests_failed:we().int().nonnegative(),elapsed_s:we().nonnegative(),step_count:we().int().nonnegative(),unmapped_count:we().int().nonnegative(),failed_count:we().int().nonnegative()}),fM=rt({format:Cs(uM),version:Cs(Od),database:ie(),runs:tt(Fd),notes:tt(ie())}),pM=rt({order:we().int().nonnegative(),object_key:ie(),unique_id:ie(),node_kind:ie(),status:ie(),execution_time_s:we(),depends_on:tt(ie())}),mM=rt({unique_id:ie(),node_kind:ie(),status:ie(),execution_time_s:we()}),gM=rt({object_key:ie(),order:we().int().nonnegative(),skipped:tt(ie())}),_M=rt({format:Cs(dM),version:Cs(Od),run:Fd,order_source:ie(),note:ie(),steps:tt(pM),unmapped:tt(mM),failure_cascade:tt(gM)}),vM=new Set(["error","fail","failure","runtime error"]),xM=new Set(["skipped","skip"]);function tc(i){const e=i.trim().toLowerCase();return vM.has(e)?"failed":xM.has(e)?"skipped":"other"}function yM(i){return tc(i)==="failed"}function kd(i){return tc(i)==="skipped"}function Au(i){return[...i].sort((e,t)=>Number(e.ok)-Number(t.ok)||t.started_at.localeCompare(e.started_at)||e.id.localeCompare(t.id))}async function bM(i="./runs.json"){const e=await fetch(i);if(!e.ok)throw new Error(`fetching ${i}: HTTP ${e.status}`);return fM.parse(await e.json())}async function MM(i,e="./runs/"){const t=`${e}${encodeURIComponent(i)}.json`,n=await fetch(t);if(!n.ok)throw new Error(`fetching ${t}: HTTP ${n.status}`);return _M.parse(await n.json())}const SM={pending:0,building:.55,built:1,failed:1,skipped:.28};class EM{constructor(){Q(this,"doc",null);Q(this,"index",new Map);Q(this,"dimsAt",new Map);Q(this,"cursor",0)}load(e){this.doc=e,this.index=new Map(e.steps.map((t,n)=>[t.object_key,n])),this.dimsAt=wM(e,this.index),this.cursor=0}exit(){this.doc=null,this.index=new Map,this.dimsAt=new Map,this.cursor=0}reset(){this.cursor=0}get phase(){return this.doc?this.cursor>=this.doc.steps.length?"done":"playing":"off"}get at(){return this.cursor}get total(){var e;return((e=this.doc)==null?void 0:e.steps.length)??0}get document(){return this.doc}current(){var e;return((e=this.doc)==null?void 0:e.steps[this.cursor])??null}stepForward(){this.jumpTo(this.cursor+1)}stepBack(){this.jumpTo(this.cursor-1)}jumpTo(e){this.doc&&(this.cursor=Math.min(Math.max(0,Math.trunc(e)),this.doc.steps.length))}stateOf(e){if(!this.doc)return"built";const t=this.index.get(e);if(t===void 0)return"built";const n=this.doc.steps[t].status;if(t<=this.cursor)return yM(n)?"failed":kd(n)?"skipped":t===this.cursor?"building":"built";const s=this.dimsAt.get(e);return s!==void 0&&this.cursor>=s.at?"skipped":"pending"}failedKeys(){const e=new Set;if(!this.doc)return e;for(const t of this.doc.steps)this.stateOf(t.object_key)==="failed"&&e.add(t.object_key);return e}skippedKeys(){const e=new Set;if(!this.doc)return e;for(const t of this.doc.steps)this.stateOf(t.object_key)==="skipped"&&e.add(t.object_key);return e}cascadeOf(e){return[...this.dimsAt.entries()].filter(([,t])=>t.by===e).map(([t])=>t).sort()}blamedFor(e){if(this.stateOf(e)!=="skipped")return null;const t=this.dimsAt.get(e);return t!==void 0&&this.cursor>=t.at?t.by:null}heightFactors(e){return e.map(t=>SM[this.stateOf(t)])}}function wM(i,e){const t=new Map;for(const n of i.failure_cascade)for(const s of n.skipped){const r=e.get(s);if(r===void 0||!kd(i.steps[r].status)||r<=n.order)continue;const a=t.get(s);(a===void 0||n.order<a.at)&&t.set(s,{at:n.order,by:n.object_key})}return t}class TM{constructor(e){Q(this,"root");Q(this,"index",null);Q(this,"error",null);this.deps=e,this.root=document.getElementById("run-panel"),window.addEventListener("keydown",t=>this.handleKey(t))}get visible(){return!this.root.hidden}async open(){if(this.root.hidden=!1,this.index===null&&this.error===null){this.render();try{this.index=await this.deps.loadIndex()}catch(e){this.error=String(e)}}this.render()}close(){this.root.hidden=!0}firstRunId(){var e;return(e=this.index)!=null&&e.runs.length?Au(this.index.runs)[0].id:null}noteError(e){this.error=e,this.root.hidden=!1,this.render()}handleKey(e){var s;const t=(s=e.target)==null?void 0:s.tagName;if(t==="INPUT"||t==="TEXTAREA")return;const n=this.deps.replay;if(n.phase!=="off"){if(e.key===" "||e.key==="ArrowRight")e.preventDefault(),n.stepForward();else if(e.key==="ArrowLeft")e.preventDefault(),n.stepBack();else if(e.key==="0")n.reset();else if(e.key==="Escape"){this.deps.onExit();return}else return;this.deps.onChange()}}render(){var e;this.root.innerHTML=this.deps.replay.phase==="off"?this.pickerHtml():this.stepHtml(),(e=this.root.querySelector(".close"))==null||e.addEventListener("click",()=>{this.deps.replay.phase==="off"?this.close():this.deps.onExit()});for(const t of this.root.querySelectorAll("[data-run]"))t.addEventListener("click",()=>void this.deps.onPick(t.dataset.run));for(const t of this.root.querySelectorAll("[data-aggregate]"))t.addEventListener("click",()=>this.deps.aggregate().start());for(const t of this.root.querySelectorAll("[data-key]"))t.addEventListener("click",()=>this.deps.onVisit(t.dataset.key))}pickerHtml(){const e='<button class="close" title="close">×</button><h3>run replay</h3>';if(this.error!==null)return`${e}<p class="none">run replay unavailable — ${Gt(this.error)}</p>`;if(this.index===null)return`${e}<p class="none">reading runs.json…</p>`;const t=this.index.notes.length?`<ul class="run-notes">${this.index.notes.map(s=>`<li>${Gt(s)}</li>`).join("")}</ul>`:"";if(!this.index.runs.length)return`${e}<p class="none">run replay unavailable — ${Gt(AM(this.index.notes))}</p>${t}${this.aggregateHtml()}`;const n=Au(this.index.runs).map(s=>{const r=s.ok?'<span class="tests-pass">● ok</span>':`<span class="tests-fail">● ${s.failed_count} failed here</span>`;return`<li data-run="${Gt(s.id)}"><b>${Gt(s.command)} · ${Gt(Ru(s.started_at))}</b><span class="badges">${r}<span class="prov">${s.step_count} steps · ${s.elapsed_s.toFixed(1)}s · ${Gt(s.target)}</span></span></li>`}).join("");return`${e}<ul class="runs">${n}</ul>${t}<p class="note">Pick a run to walk it step by step. "failed here" counts failing steps with a building on this map — dbt's own totals sit beside it in the step header.</p>${this.aggregateHtml()}`}aggregateHtml(){const e=this.deps.aggregate();return e.available?`<h3>no run named</h3><ul class="runs"><li data-aggregate="1"><b>aggregate schedule</b><span class="badges"><span class="prov">newest status per node · ${Gt(e.note)}</span></span></li></ul>`:""}stepHtml(){const e=this.deps.replay,t=e.document,n=t.run,s=`<button class="close" title="exit replay">×</button><h3>run replay · ${e.phase==="done"?"finished":`step ${e.at+1} / ${e.total}`}</h3><p class="run-head"><b>${Gt(n.command)} · ${Gt(Ru(n.started_at))}</b><span class="prov">${Gt(n.target)} · ${n.models_error} model errors, ${n.tests_failed} tests failed · ${n.unmapped_count} nodes off this map</span></p>`,r=`<p class="keys">space / → next · ← back · 0 restart · esc exit</p><p class="note">${Gt(t.note)} (order ${Gt(t.order_source)}).</p>`,a=e.current();if(a===null){const p=[...e.failedKeys()],g=[...e.skippedKeys()];return`${s}<p class="none">the run is over.</p><dl><dt>burning</dt><dd>${cs(p)}</dd><dt>skipped</dt><dd>${cs(g)}</dd></dl>${r}`}const o=tc(a.status),l=o==="failed"?"tests-fail":o==="skipped"?"prov":"tests-pass",c=e.cascadeOf(a.object_key),h=o==="failed"?`<p class="cascade"><b>${Gt(a.object_key)} errored here.</b> `+(c.length?`dbt reported ${c.length} downstream model${c.length===1?"":"s"} skipped: ${cs(c)}`:"nothing measurable cascaded from it.")+"</p>":"",d=e.blamedFor(a.object_key),u=d?`<p class="cascade">skipped — dbt did not run it after ${cs([d])} errored.</p>`:"";return`${s}<dl><dt>step</dt><dd>${cs([a.object_key])}</dd><dt>status</dt><dd class="${l}">${Gt(a.status)}</dd><dt>kind</dt><dd>${Gt(a.node_kind||"—")}</dd><dt>took</dt><dd>${a.execution_time_s.toFixed(2)} s <span class="prov">measured</span></dd><dt>upstream</dt><dd>${a.depends_on.length?cs(a.depends_on):"<span class='prov'>none on this map</span>"}</dd></dl>${h}${u}${r}`}}function cs(i){return i.length?i.map(e=>`<span class="door" data-key="${Gt(e)}">${Gt(e)}</span>`).join(" "):"<span class='prov'>none</span>"}function AM(i){return i.some(e=>/locked/i.test(e))?"run metadata locked":i.some(e=>/no run metadata/i.test(e))?"no run metadata":i.some(e=>/no dbt run history/i.test(e))?"no dbt run history for this catalog":i.some(e=>/no run history/i.test(e))?"no run history yet":"no runs to replay"}function Ru(i){return i.replace("T"," ").slice(0,16)}function Gt(i){return i.replace(/[&<>"']/g,e=>`&#${e.charCodeAt(0)};`)}function RM(i){const e=new EM,t=new TM({replay:e,loadIndex:()=>bM("./runs.json"),onPick:o=>n(o),onExit:()=>{e.exit(),s()},onChange:()=>s(),onVisit:i.visit,aggregate:()=>({available:i.city().replay.available,note:i.city().replay.note,start:()=>{i.city().replay.start(),i.setStatus(`replaying last run — ${i.city().replay.note}`)}})});async function n(o){try{e.load(await MM(o))}catch(l){t.noteError(String(l));return}s()}function s(){const o=i.city();if(e.phase==="off"){o.buildings.setReplayProgress(null),o.fires.setOverride(null),o.trucks.setOverride(null),o.traffic.setOverride(null),i.setStatus(null),t.render();return}const l=i.doc();o.buildings.setReplayProgress(e.heightFactors(l.lots.map(u=>u.object_key)));const c=e.failedKeys();o.fires.setOverride(c),o.trucks.setOverride(c),o.traffic.setOverride(CM(l,e));const h=e.current();h&&i.visit(h.object_key);const d=e.document.run;i.setStatus(e.phase==="done"?`replay finished — ${d.command} ${d.id} — ${e.document.note}`:`replaying ${d.command} ${d.id} — step ${e.at+1}/${e.total} — ${e.document.note}`),t.render()}async function r(o){await t.open();const l=o??t.firstRunId();l!=null&&await n(l)}return document.getElementById("replay-button").addEventListener("click",()=>{t.visible&&e.phase==="off"?t.close():t.open()}),{replay:e,panel:t,apply:s,start:r}}function CM(i,e){const t=e.current();if(!t)return[];const n=new Set(t.depends_on);return i.edges.filter(s=>s.dst===t.object_key&&n.has(s.src)&&s.route.length>0).map(s=>s.route.map(([r,a])=>[r,a]))}class PM{constructor(e,t,n,s,r,a){Q(this,"raycaster",new vp);Q(this,"pointer",new Fe);Q(this,"targets");this.buildings=e,this.camera=n,this.dom=s,this.targets=[e.mesh,t];let o=null;s.addEventListener("pointerdown",l=>o={x:l.clientX,y:l.clientY}),s.addEventListener("pointerup",l=>{const c=o&&Math.hypot(l.clientX-o.x,l.clientY-o.y)>5;o=null,c||a(this.resolve(l))}),s.addEventListener("pointermove",l=>r(this.resolve(l)))}setTargets(e,t,n=[]){this.buildings=e,this.targets=[e.mesh,t,...n]}resolve(e){var s;const t=this.dom.getBoundingClientRect();this.pointer.set((e.clientX-t.left)/t.width*2-1,-((e.clientY-t.top)/t.height)*2+1),this.raycaster.setFromCamera(this.pointer,this.camera);const n=this.raycaster.intersectObjects(this.targets,!0)[0];return n?typeof n.object.userData.key=="string"?n.object.userData.key:n.instanceId!==void 0&&n.object===this.buildings.mesh?((s=this.buildings.lots[n.instanceId])==null?void 0:s.object_key)??null:null:null}}function LM(i,e,t,n){const{doc:s,city:r,app:a}=i,o=document.getElementById("status"),l=j=>`database: ${j.database.name}   ·   ${j.database.object_count} objects   ·   ${j.database.total_rows.toLocaleString()} rows`;let c=l(s);o.textContent=c,o.title=c;const h=document.getElementById("notes-button"),d=document.getElementById("notes-pop");function u(j){const Ne=[...j.database.has_known_edges?[]:["no lineage detected"],...j.database.notes];h.hidden=Ne.length===0,h.textContent=`ⓘ notes (${Ne.length})`,d.innerHTML=`<b>degradation notes</b><ul>${Ne.map(ze=>`<li>${ze}</li>`).join("")}</ul>`}u(s),document.getElementById("notes-button").addEventListener("click",()=>{const j=document.getElementById("notes-pop");j.hidden=!j.hidden,document.getElementById("keys-pop").hidden=!0});const p=document.getElementById("keys-pop");p.innerHTML=`<table>
    <tr><td>/</td><td>search</td></tr>
    <tr><td>P</td><td>problems panel</td></tr>
    <tr><td>?lens=…</td><td>role lens (footer switcher; presentation only)</td></tr>
    <tr><td>?tour=1</td><td>guided tour — enter/n next, esc skip</td></tr>
    <tr><td>space / →</td><td>replay: next step</td></tr>
    <tr><td>←</td><td>replay: previous step</td></tr>
    <tr><td>0</td><td>replay: back to step 1</td></tr>
    <tr><td>esc</td><td>replay: exit</td></tr>
    <tr><td>T</td><td>toggle the road-load overlay</td></tr>
    <tr><td>W</td><td>toggle the weather overlay (source freshness)</td></tr>
    <tr><td>U</td><td>toggle the usage overlay (measured run appearances)</td></tr>
    <tr><td>R</td><td>re-read the catalog in place</td></tr>
    <tr><td>F</td><td>fly camera</td></tr>
    <tr><td>H</td><td>home framing</td></tr>
    <tr><td>drag / wheel</td><td>orbit / zoom</td></tr>
    <tr><td>click</td><td>inspect a building</td></tr></table>`,document.getElementById("keys-button").addEventListener("click",()=>{p.hidden=!p.hidden,document.getElementById("notes-pop").hidden=!0});const g=document.getElementById("asof");let x={kind:"fetched",at:Date.now()};function m(){g.textContent=xb(x,Date.now()),g.title=yb(x)}async function f(j,Ne=!1){const ze=Ne?`./meta.json?t=${j}`:"./meta.json";x=await _b(ze,j),m()}m(),setInterval(m,1e3),f(Date.now());const M=i.vehicleLayer,E=i.guestLayer;let y=null,T=s;const S={current:i.city};function R(j){y=j,$.show(j),v.setSelection(j);const Ne=T.lots.find(ze=>ze.object_key===j);Ne?(V.visible=!0,V.scale.set(Ne.w-.22,S.current.buildings.heightOf(Ne)+.06,Ne.h-.22),V.position.set(Ne.x+Ne.w/2,0,Ne.y+Ne.h/2)):j===mi?(V.visible=!0,V.scale.set(1.5,4,1.5),V.position.set(T.plant.x+.5,0,T.plant.y+.5)):j===xs&&T.library?(V.visible=!0,V.scale.set(1.7,1.1,1.3),V.position.set(T.library.x+.5,0,T.library.y+.5)):j===or&&T.firehouse?(V.visible=!0,V.scale.set(1.6,1.3,1.2),V.position.set(T.firehouse.x+.5,0,T.firehouse.y+.5)):V.visible=!1}const v=new Mb(s);e.add(v.group);const w=new Tb;w.build(s),e.add(w.group);const C=new Cb;C.build(s),e.add(C.group);const L=new Bb;L.build(s),e.add(L.group);const N=new zb;N.register(w),N.register(C),N.register(L);const V=new Yu(new Ju(new Tt(1,1,1).translate(0,.5,0)),new Vl({color:Ox}));V.visible=!1,e.add(V);const $=new $b(s,j=>R(j||null)),F=new qb(s,j=>R(j)),W=new ay(s,j=>oe(j)),G=new eM(s,j=>oe(j)),J=t.get("crlf")==="1"?new tM:null;J&&J.load("./requests.json");const te=new nM(s,j=>oe(j));Su(s);function oe(j){const Ne=S.current,ze=T,ut=j===mi?ze.plant:j===xs?ze.library:j===or?ze.firehouse:null;if(ut){i.camera.flyTo(ut.x+.5,ut.y+.5,3),R(j);return}const xt=ze.lots.find(It=>It.object_key===j);xt&&(i.camera.flyTo(xt.x+xt.w/2,xt.y+xt.h/2,Ne.buildings.heightOf(xt)),R(j))}const me=sy(t.get("lens"),Eu);let be=me.lens;const at=new rM(j=>gt(j,!0));function gt(j,Ne){be=j,Ne&&Eu.write(j.id),at.setLens(j),W.setLens(j),G.setLens(j),N.applyLens(j),j.defaultPanel==="library"&&T.library?R(xs):j.defaultPanel!=="none"&&G.show()}gt(be,!1),me.firstRun&&!t.get("settle")&&t.get("lens")===null&&new sM(j=>gt(j,!0)).open();const it=t.get("selected");it&&R(it);const Y=new hM({doc:()=>T,visit:oe,lens:()=>be,setOverlay:j=>{var Ne;return(Ne=N.get(j))==null?void 0:Ne.setVisible(!0)}}),ae=t.get("tour");ae!==null&&ae!=="0"&&Y.start(ae==="restart");const ne=RM({doc:()=>T,city:()=>S.current,visit:oe,setStatus:j=>{o.textContent=j??c,o.title=o.textContent}}),Oe=document.getElementById("tooltip"),Ve=new PM(S.current.buildings,S.current.plant,i.camera.camera,a,j=>{if(j===null||j===mi){Oe.hidden=!0,a.style.cursor=j===null?"default":"pointer";return}Oe.hidden=!1,Oe.textContent=`${j} — ${(S.current.rows.get(j)??0).toLocaleString()} rows`,a.style.cursor="pointer"},R);Ve.setTargets(S.current.buildings,S.current.plant,S.current.civicTargets),a.addEventListener("pointermove",j=>{Oe.style.left=`${j.clientX+14}px`,Oe.style.top=`${j.clientY+14}px`});let Ie=!1;async function Et(){if(!Ie){Ie=!0,o.textContent="refreshing…";try{const j=await mb(async()=>{const{loadCity:ut}=await Promise.resolve().then(()=>sx);return{loadCity:ut}},void 0,import.meta.url).then(({loadCity:ut})=>ut(`./city.json?t=${Date.now()}`)),Ne=Date.now(),ze=y;R(null),ub(e,S.current,[M.mesh,E.mesh]),S.current=await Id(e,j,n),T=j,Ve.setTargets(S.current.buildings,S.current.plant,S.current.civicTargets),$.setDoc(j),F.setDoc(j),W.setDoc(j),G.setDoc(j),te.setDoc(j),v.setDoc(j),w.build(j),C.build(j),L.build(j),Je(j),f(Ne,!0),ne.apply(),ze&&(ze===mi||j.lots.some(ut=>ut.object_key===ze))&&R(ze)}catch(j){o.textContent=`refresh failed: ${String(j)} — showing previous city`,o.title=o.textContent,setTimeout(()=>{o.textContent=c,o.title=c},6e3),Ie=!1;return}Ie=!1}}function Je(j){document.getElementById("logo").textContent=j.theme.logo_text,c=l(j),o.textContent=c,o.title=c,u(j),Su(j)}return window.__tycoonCityRefresh=()=>void Et(),{status:o,statusLine:()=>c,asof:g,doc:()=>T,city:()=>S.current,camera:i.camera,skybridges:v,flow:w,weather:C,usage:L,overlays:N,outline:V,inspector:$,stats:F,health:W,problems:G,requests:J,search:te,selected:()=>y,select:R,visit:oe,lens:()=>be,setLens:j=>gt(j==="none"?Qn:gi[j],!1),tour:Y,run:ne,picking:Ve,tooltip:Oe,refresh:Et}}function DM(i,e,t,n){const{renderer:s,labels:r,camera:a}=i;window.addEventListener("keydown",l=>{var h;const c=(h=l.target)==null?void 0:h.tagName;c==="INPUT"||c==="TEXTAREA"||((l.key==="r"||l.key==="R")&&n(),(l.key==="b"||l.key==="B")&&(t==null||t.toggle()),e.handleKey(l.key))});function o(){const{clientWidth:l,clientHeight:c}=i.app;s.setSize(l,c),r.setSize(l,c),a.resize(l,c)}window.addEventListener("resize",o),o()}function IM(i,e,t,n){const{renderer:s,labels:r,scene:a,camera:o,guests:l,vehicleLayer:c,guestLayer:h}=i,{city:d,flow:u,weather:p,usage:g,run:x,status:m,statusLine:f}=e,M=new xp;let E=0;s.setAnimationLoop(()=>{const y=M.getDelta();if(o.tick(y),d().buildings.tick(y),t||(d().fires.tick(y),d().trucks.tick(y),d().vans.tick(y),p.tick(y),g.tick(y)),!t){for(E+=y;E>=vo;){if(d().traffic.tick(),n&&l.tick(),d().replay.active){const S=d().replay.tick();d().buildings.setReplayProgress(S),S===null&&(m.textContent=f(),m.title=f())}E-=vo}const T=E/vo;c.update(d().traffic,T),n&&h.update(l,T)}s.render(a,o.camera),r.render(a,o.camera),document.body.dataset.ready="1"})}function NM(i){const{cameras:e,renderer:t,scene:n,skybridges:s,flow:r,weather:a,usage:o}=i,l={get doc(){return i.doc()},sceneChildCount:()=>n.children.length,select:i.select,selectedKey:i.selectedKey,vehicleCount:i.vehicleCount,guestCount:i.guestCount,skybridgeCount:()=>s.count,flowTileCount:()=>r.count,weatherMeshCount:()=>a.meshCount,weatherSchemas:()=>a.weatheredSchemas,weatherElapsed:()=>a.elapsed,weatherVisible:()=>a.visible,flowVisible:()=>r.visible,usageVisible:()=>o.visible,usageInstanceCount:()=>o.instanceCount,usagePainted:c=>o.keysPainted(c),usageElapsed:()=>o.elapsed,fireCount:()=>i.city().fires.count,truckCount:()=>i.city().trucks.count,vanCount:()=>i.city().vans.count,wearCount:()=>i.city().wear.count,curbCount:()=>{var c;return((c=i.city().streetscape)==null?void 0:c.curbCount)??0},streetFeatureCount:()=>{var c;return((c=i.city().streetscape)==null?void 0:c.featureCount)??0},setPose:c=>e.setPose(c),visit:i.visit,cameraPose:()=>e.serialize(),setCameraPose:c=>e.restore(c),refresh:i.refresh,lensId:i.lensId,setLens:i.setLens,runReplay:c=>i.run.start(c),runStateOf:c=>i.run.replay.stateOf(c),runStep:()=>{i.run.replay.stepForward(),i.run.apply()},runCursor:()=>{var c;return{phase:i.run.replay.phase,at:i.run.replay.at,total:i.run.replay.total,key:((c=i.run.replay.current())==null?void 0:c.object_key)??null}},screenPos:c=>{const h=i.doc(),d=h.lots.find(g=>g.object_key===c),u=d?new P(d.x+d.w/2,i.city().buildings.heightOf(d)/2,d.y+d.h/2):c===mi?new P(h.plant.x+.5,1.6,h.plant.y+.5):null;if(!u||(u.project(e.camera),u.z>1))return null;const p=t.domElement.getBoundingClientRect();return{x:p.left+(u.x+1)/2*p.width,y:p.top+(1-u.y)/2*p.height}},districtScreenRect:c=>{const h=i.doc().districts.find(p=>p.schema===c);if(!h)return null;const d=t.domElement.getBoundingClientRect(),u=[[h.x,h.y],[h.x+h.w,h.y],[h.x,h.y+h.h],[h.x+h.w,h.y+h.h]].map(([p,g])=>{const x=new P(p,0,g).project(e.camera);return{x:d.left+(x.x+1)/2*d.width,y:d.top+(1-x.y)/2*d.height}});return{left:Math.min(...u.map(p=>p.x)),top:Math.min(...u.map(p=>p.y)),right:Math.max(...u.map(p=>p.x)),bottom:Math.max(...u.map(p=>p.y))}}};return window.__tycoonCity=l,l}async function UM(){const i=new URLSearchParams(window.location.search),e=i.get("settle")==="1",t=i.get("guests")==="1";let n,s,r;try{n=await db(i),r={flat:i.get("flat")==="1",settle:i.get("settle")==="1",ambient:i.get("ambient")==="1",seedFor:n.seedFor},s=LM(n,n.scene,i,r)}catch(c){document.getElementById("status").textContent=String(c),console.error(c);return}const a=()=>s.refresh();DM(n,s.overlays,s.requests,a),IM(n,s,e,t);const o=s.run,l=NM({doc:()=>s.doc(),city:()=>s.city(),cameras:n.camera,renderer:n.renderer,scene:n.scene,skybridges:s.skybridges,flow:s.flow,weather:s.weather,usage:s.usage,vehicleCount:()=>n.vehicleLayer.mesh.count,guestCount:()=>n.guestLayer.mesh.count,selectedKey:s.selected,select:c=>s.select(c||null),visit:s.visit,refresh:a,run:o,lensId:()=>s.lens().id,setLens:s.setLens});window.__tycoonCity=l}UM().catch(i=>{document.getElementById("status").textContent=String(i),console.error(i)});
