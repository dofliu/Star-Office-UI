// DofLab Office UI - 佈局與層級配置
// 所有座標、depth、資源路徑統一管理在這裡
// 避免 magic numbers，降低改錯風險

// 核心規則：
// - 透明資源（如辦公桌）強制 .png，不透明優先 .webp
// - 層級：低 → sofa(10) → starWorking(900) → desk(1000) → flower(1100)

// === 場景定義 ===
const SCENES = {
  // 場景1：主辦公室（研究與開發）
  mainOffice: {
    name: '主辦公室',
    description: '研究與開發區域',
    background: 'office_bg_small',
    areas: {
      door:        { x: 640, y: 550 },
      writing:     { x: 320, y: 360 },
      researching: { x: 320, y: 360 },
      error:       { x: 1066, y: 180 },
      breakroom:   { x: 640, y: 360 }
    },
    furniture: {
      sofa: { x: 670, y: 144, origin: { x: 0, y: 0 }, depth: 10 },
      desk: { x: 218, y: 417, origin: { x: 0.5, y: 0.5 }, depth: 1000 },
      flower: { x: 310, y: 390, origin: { x: 0.5, y: 0.5 }, depth: 1100, scale: 0.8 },
      starWorking: { x: 217, y: 333, origin: { x: 0.5, y: 0.5 }, depth: 900, scale: 1.32 },
      coffeeMachine: { x: 659, y: 397, origin: { x: 0.5, y: 0.5 }, depth: 99 },
      serverroom: { x: 1021, y: 142, origin: { x: 0.5, y: 0.5 }, depth: 2 },
      errorBug: { x: 1007, y: 221, origin: { x: 0.5, y: 0.5 }, depth: 50, scale: 0.9, pingPong: { leftX: 1007, rightX: 1111, speed: 0.6 } },
      syncAnim: { x: 1157, y: 592, origin: { x: 0.5, y: 0.5 }, depth: 40 },
      cat: { x: 94, y: 557, origin: { x: 0.5, y: 0.5 }, depth: 2000 },
      poster: { x: 252, y: 66, depth: 4 },
      plants: [
        { x: 565, y: 178, depth: 5 },
        { x: 230, y: 185, depth: 5 },
        { x: 977, y: 496, depth: 5 }
      ]
    }
  },
  
  // 場景2：創意工作室（設計與規劃）
  creativeStudio: {
    name: '創意工作室',
    description: '設計與規劃區域',
    background: 'office_bg_small',
    areas: {
      door:        { x: 640, y: 550 },
      writing:     { x: 500, y: 360 },
      researching: { x: 500, y: 360 },
      error:       { x: 1066, y: 180 },
      breakroom:   { x: 800, y: 360 }
    },
    furniture: {
      sofa: { x: 800, y: 144, origin: { x: 0, y: 0 }, depth: 10 },
      desk: { x: 400, y: 417, origin: { x: 0.5, y: 0.5 }, depth: 1000 },
      flower: { x: 500, y: 390, origin: { x: 0.5, y: 0.5 }, depth: 1100, scale: 0.8 },
      starWorking: { x: 400, y: 333, origin: { x: 0.5, y: 0.5 }, depth: 900, scale: 1.32 },
      coffeeMachine: { x: 900, y: 397, origin: { x: 0.5, y: 0.5 }, depth: 99 },
      serverroom: { x: 1100, y: 142, origin: { x: 0.5, y: 0.5 }, depth: 2 },
      errorBug: { x: 1007, y: 221, origin: { x: 0.5, y: 0.5 }, depth: 50, scale: 0.9, pingPong: { leftX: 1007, rightX: 1111, speed: 0.6 } },
      syncAnim: { x: 1157, y: 592, origin: { x: 0.5, y: 0.5 }, depth: 40 },
      cat: { x: 200, y: 557, origin: { x: 0.5, y: 0.5 }, depth: 2000 },
      poster: { x: 252, y: 66, depth: 4 },
      plants: [
        { x: 600, y: 200, depth: 5 },
        { x: 300, y: 180, depth: 5 },
        { x: 900, y: 500, depth: 5 }
      ]
    }
  },
  
  // 場景3：會議室（討論與協作）
  meetingRoom: {
    name: '會議室',
    description: '討論與協作區域',
    background: 'office_bg_small',
    areas: {
      door:        { x: 640, y: 550 },
      writing:     { x: 640, y: 360 },
      researching: { x: 640, y: 360 },
      error:       { x: 1066, y: 180 },
      breakroom:   { x: 400, y: 360 }
    },
    furniture: {
      sofa: { x: 400, y: 144, origin: { x: 0, y: 0 }, depth: 10 },
      desk: { x: 640, y: 417, origin: { x: 0.5, y: 0.5 }, depth: 1000 },
      flower: { x: 700, y: 390, origin: { x: 0.5, y: 0.5 }, depth: 1100, scale: 0.8 },
      starWorking: { x: 640, y: 333, origin: { x: 0.5, y: 0.5 }, depth: 900, scale: 1.32 },
      coffeeMachine: { x: 300, y: 397, origin: { x: 0.5, y: 0.5 }, depth: 99 },
      serverroom: { x: 900, y: 142, origin: { x: 0.5, y: 0.5 }, depth: 2 },
      errorBug: { x: 1007, y: 221, origin: { x: 0.5, y: 0.5 }, depth: 50, scale: 0.9, pingPong: { leftX: 1007, rightX: 1111, speed: 0.6 } },
      syncAnim: { x: 1157, y: 592, origin: { x: 0.5, y: 0.5 }, depth: 40 },
      cat: { x: 1000, y: 557, origin: { x: 0.5, y: 0.5 }, depth: 2000 },
      poster: { x: 252, y: 66, depth: 4 },
      plants: [
        { x: 500, y: 180, depth: 5 },
        { x: 800, y: 200, depth: 5 },
        { x: 1100, y: 500, depth: 5 }
      ]
    }
  }
};

// 當前場景 - 與 index.html 的 currentSceneId 同步
let currentSceneId = localStorage.getItem('starOfficeScene') || 'mainOffice';

// 獲取當前場景配置
function getCurrentScene() {
  return SCENES[currentSceneId] || SCENES.mainOffice;
}

// 獲取場景配置（供外部呼叫）
function getSceneConfig() {
  return getCurrentScene();
}

// 切換場景
function switchScene(sceneId) {
  if (SCENES[sceneId]) {
    currentSceneId = sceneId;
    localStorage.setItem('starOfficeScene', sceneId);
    return true;
  }
  return false;
}

const LAYOUT = {
  // === 遊戲畫布 ===
  game: {
    width: 1280,
    height: 720
  },

  // === 各區域座標 ===
  get areas() {
    return getCurrentScene().areas;
  },

  // === 裝飾與傢俱：座標 + 原點 + depth ===
  get furniture() {
    return getCurrentScene().furniture;
  },

  // === 牌匾 ===
  plaque: {
    x: 640,
    y: 720 - 36,
    width: 420,
    height: 44
  },

  // === 資源載入規則：哪些強制用 PNG（透明資源） ===
  forcePng: {
    desk_v2: true // 新辦公桌必須透明，強制 PNG
  },

  // === 總資源數量（用於載入進度條） ===
  totalAssets: 15
};
