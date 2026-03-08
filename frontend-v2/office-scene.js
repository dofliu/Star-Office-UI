/**
 * Star Office — Phaser 3 Pixel Dashboard
 * Renders AI agents in a 2D pixel office with real-time status polling.
 */

// --- Color palette ---
const COLORS = {
    bg:        0x0f0e17,
    panel:     0x1a1a2e,
    border:    0x2e2e4a,
    accent:    0x7f5af0,
    green:     0x2cb67d,
    red:       0xff6b6b,
    orange:    0xf9a825,
    cyan:      0x72f1d4,
    text:      0xfffffe,
    textDim:   0x94a1b2,
    yellow:    0xffd700,
};

// State → color mapping
const STATE_COLORS = {
    idle:        COLORS.textDim,
    writing:     COLORS.accent,
    researching: COLORS.cyan,
    executing:   COLORS.green,
    syncing:     COLORS.orange,
    error:       COLORS.red,
};

// State → icon
const STATE_ICONS = {
    idle:        '💤',
    writing:     '✍️',
    researching: '🔍',
    executing:   '⚡',
    syncing:     '🔄',
    error:       '🐛',
};

// Avatar → color for pixel character rendering
const AVATAR_COLORS = {
    char_blue:   0x4a90d9,
    char_green:  0x2cb67d,
    char_red:    0xe74c3c,
    char_purple: 0x7f5af0,
    char_orange: 0xf39c12,
    char_cyan:   0x72f1d4,
    char_pink:   0xff69b4,
    char_yellow: 0xffd700,
};

const CANVAS_W = 960;
const CANVAS_H = 540;
const POLL_INTERVAL = 3000; // ms
const AGENT_CARD_W = 200;
const AGENT_CARD_H = 180;
const CARD_MARGIN = 16;

class OfficeScene extends Phaser.Scene {
    constructor() {
        super({ key: 'OfficeScene' });
        this.agentData = [];
        this.agentSprites = {};  // agentId -> { container, ... }
        this.pollTimer = null;
    }

    preload() {
        // We draw everything procedurally — no external assets needed for v2
    }

    create() {
        window.starOfficeScene = this;
        this.currentZoom = 1.0;

        // Background: dark gradient feel with pixel grid
        this.drawBackground();

        // Title bar
        this.add.text(CANVAS_W / 2, 18, '⭐ STAR OFFICE', {
            fontSize: '20px',
            fontFamily: "'ArkPixel', 'Courier New', monospace",
            color: '#7f5af0',
        }).setOrigin(0.5, 0);

        // Subtitle
        this.statusText = this.add.text(CANVAS_W / 2, 42, 'Connecting...', {
            fontSize: '12px',
            fontFamily: "'ArkPixel', 'Courier New', monospace",
            color: '#94a1b2',
        }).setOrigin(0.5, 0);

        // Office floor area
        this.drawOfficeFloor();

        // Start polling
        this.fetchAgents();
        this.pollTimer = this.time.addEvent({
            delay: POLL_INTERVAL,
            callback: () => this.fetchAgents(),
            loop: true,
        });

        // Add agent button
        this.drawAddButton();

        // Zoom controls
        this.drawZoomControls();
    }

    drawBackground() {
        // Main bg
        this.add.rectangle(CANVAS_W / 2, CANVAS_H / 2, CANVAS_W, CANVAS_H, COLORS.bg);

        // Subtle pixel grid
        const gfx = this.add.graphics();
        gfx.lineStyle(1, 0x1a1a2e, 0.3);
        for (let x = 0; x < CANVAS_W; x += 32) {
            gfx.moveTo(x, 0);
            gfx.lineTo(x, CANVAS_H);
        }
        for (let y = 0; y < CANVAS_H; y += 32) {
            gfx.moveTo(0, y);
            gfx.lineTo(CANVAS_W, y);
        }
        gfx.strokePath();
    }

    drawOfficeFloor() {
        // Floor area
        const floorY = 64;
        const floorH = CANVAS_H - floorY - 10;
        const gfx = this.add.graphics();
        gfx.fillStyle(0x16161a, 0.6);
        gfx.fillRoundedRect(12, floorY, CANVAS_W - 24, floorH, 8);
        gfx.lineStyle(1, COLORS.border, 0.5);
        gfx.strokeRoundedRect(12, floorY, CANVAS_W - 24, floorH, 8);

        // Zone labels
        const zones = [
            { label: '🛋 休息區 Lounge', x: 100, y: floorY + 14 },
            { label: '💻 工作區 Workspace', x: CANVAS_W / 2, y: floorY + 14 },
            { label: '🐛 Debug Corner', x: CANVAS_W - 100, y: floorY + 14 },
        ];
        zones.forEach(z => {
            this.add.text(z.x, z.y, z.label, {
                fontSize: '10px',
                fontFamily: "'ArkPixel', 'Courier New', monospace",
                color: '#94a1b2',
            }).setOrigin(0.5, 0);
        });
    }

    drawAddButton() {
        const bx = CANVAS_W - 50;
        const by = 24;
        const btn = this.add.graphics();
        btn.fillStyle(COLORS.accent, 1);
        btn.fillRoundedRect(bx - 30, by - 12, 60, 24, 6);

        const txt = this.add.text(bx, by, '＋ Add', {
            fontSize: '11px',
            fontFamily: "'ArkPixel', 'Courier New', monospace",
            color: '#ffffff',
        }).setOrigin(0.5, 0.5);

        // Hit area
        const hitZone = this.add.zone(bx, by, 60, 24).setInteractive({ useHandCursor: true });
        hitZone.on('pointerdown', () => this.promptAddAgent());
    }

    async fetchAgents() {
        try {
            const res = await fetch('/agents');
            const data = await res.json();
            this.agentData = data.agents || [];
            this.statusText.setText(`${this.agentData.length} agent(s) online — port 19200`);
            this.renderAgents();
            // Update sidebar and check for state changes
            if (typeof updateSidebar === 'function') updateSidebar(this.agentData);
            if (typeof checkStateChanges === 'function') checkStateChanges(this.agentData);
        } catch (e) {
            this.statusText.setText('⚠ Connection failed');
            console.error('Fetch error:', e);
        }
    }

    renderAgents() {
        // Remove old sprites
        Object.values(this.agentSprites).forEach(s => {
            if (s.container) s.container.destroy();
        });
        this.agentSprites = {};

        if (this.agentData.length === 0) {
            // Empty state
            if (!this.emptyText) {
                this.emptyText = this.add.text(CANVAS_W / 2, CANVAS_H / 2, 'No agents yet. Click ＋ Add to register one.', {
                    fontSize: '14px',
                    fontFamily: "'ArkPixel', 'Courier New', monospace",
                    color: '#94a1b2',
                }).setOrigin(0.5, 0.5);
            }
            return;
        }
        if (this.emptyText) {
            this.emptyText.destroy();
            this.emptyText = null;
        }

        // Position agents based on state
        const idleAgents = this.agentData.filter(a => a.state === 'idle');
        const workAgents = this.agentData.filter(a => ['writing', 'researching', 'executing', 'syncing'].includes(a.state));
        const errorAgents = this.agentData.filter(a => a.state === 'error');

        // Layout: idle on left, work in center, error on right
        const floorY = 90;

        idleAgents.forEach((agent, i) => {
            const x = 80 + (i % 2) * (AGENT_CARD_W + CARD_MARGIN);
            const y = floorY + 30 + Math.floor(i / 2) * (AGENT_CARD_H + CARD_MARGIN);
            this.createAgentCard(agent, x, y);
        });

        workAgents.forEach((agent, i) => {
            const startX = 320;
            const x = startX + (i % 3) * (AGENT_CARD_W + CARD_MARGIN);
            const y = floorY + 30 + Math.floor(i / 3) * (AGENT_CARD_H + CARD_MARGIN);
            this.createAgentCard(agent, x, y);
        });

        errorAgents.forEach((agent, i) => {
            const x = CANVAS_W - 180;
            const y = floorY + 30 + i * (AGENT_CARD_H + CARD_MARGIN);
            this.createAgentCard(agent, x, y);
        });
    }

    createAgentCard(agent, x, y) {
        const container = this.add.container(x, y);
        const stateColor = STATE_COLORS[agent.state] || COLORS.textDim;
        const label = agent.label || agent.name;

        // Card background
        const gfx = this.add.graphics();
        gfx.fillStyle(COLORS.panel, 0.9);
        gfx.fillRoundedRect(0, 0, AGENT_CARD_W, AGENT_CARD_H, 8);
        gfx.lineStyle(2, stateColor, 0.8);
        gfx.strokeRoundedRect(0, 0, AGENT_CARD_W, AGENT_CARD_H, 8);
        container.add(gfx);

        // Pixel character (simple procedural)
        const charGfx = this.add.graphics();
        const avatarColor = AVATAR_COLORS[agent.avatar] || AVATAR_COLORS.char_blue;
        this.drawPixelCharacter(charGfx, AGENT_CARD_W / 2 - 16, 14, avatarColor, agent.state);
        container.add(charGfx);

        // State icon
        const icon = this.add.text(AGENT_CARD_W - 24, 8, STATE_ICONS[agent.state] || '❓', {
            fontSize: '16px',
        });
        container.add(icon);

        // Pulsing effect for work states
        if (['writing', 'researching', 'executing', 'syncing'].includes(agent.state)) {
            this.tweens.add({
                targets: icon,
                alpha: { from: 1, to: 0.4 },
                duration: 800,
                yoyo: true,
                repeat: -1,
            });
        }

        // Agent label (display_name or name)
        const nameText = this.add.text(AGENT_CARD_W / 2, 80, label, {
            fontSize: '13px',
            fontFamily: "'ArkPixel', 'Courier New', monospace",
            color: '#fffffe',
            align: 'center',
            wordWrap: { width: AGENT_CARD_W - 16 },
        }).setOrigin(0.5, 0);
        container.add(nameText);

        // State label
        const stateLabel = this.add.text(AGENT_CARD_W / 2, 98, agent.state.toUpperCase(), {
            fontSize: '10px',
            fontFamily: "'ArkPixel', 'Courier New', monospace",
            color: Phaser.Display.Color.IntegerToColor(stateColor).rgba,
        }).setOrigin(0.5, 0);
        container.add(stateLabel);

        // Message
        if (agent.message) {
            const msgText = this.add.text(AGENT_CARD_W / 2, 114, agent.message, {
                fontSize: '10px',
                fontFamily: "'ArkPixel', 'Courier New', monospace",
                color: '#94a1b2',
                align: 'center',
                wordWrap: { width: AGENT_CARD_W - 20 },
            }).setOrigin(0.5, 0);
            container.add(msgText);
        }

        // Progress bar (if progress > 0)
        if (agent.progress > 0) {
            const barY = agent.message ? 138 : 118;
            const barW = AGENT_CARD_W - 32;
            const barH = 6;
            const barX = 16;
            const barBg = this.add.graphics();
            barBg.fillStyle(0x16161a, 1);
            barBg.fillRoundedRect(barX, barY, barW, barH, 3);
            container.add(barBg);
            const barFill = this.add.graphics();
            barFill.fillStyle(stateColor, 1);
            barFill.fillRoundedRect(barX, barY, barW * (agent.progress / 100), barH, 3);
            container.add(barFill);
            const pctText = this.add.text(AGENT_CARD_W - 16, barY - 1, `${agent.progress}%`, {
                fontSize: '8px',
                fontFamily: "'ArkPixel', 'Courier New', monospace",
                color: '#94a1b2',
            }).setOrigin(1, 0);
            container.add(pctText);
        }

        // ID badge (small, bottom)
        const idBadge = this.add.text(AGENT_CARD_W / 2, AGENT_CARD_H - 14, `#${agent.id}`, {
            fontSize: '9px',
            fontFamily: "'ArkPixel', 'Courier New', monospace",
            color: '#555',
        }).setOrigin(0.5, 0);
        container.add(idBadge);

        // Settings gear button (top-left)
        const gear = this.add.text(8, 6, '⚙', { fontSize: '14px' }).setInteractive({ useHandCursor: true });
        gear.on('pointerdown', (pointer) => {
            pointer.event.stopPropagation();
            if (typeof openSettings === 'function') {
                openSettings(agent.id, agent.display_name, agent.avatar);
            }
        });
        container.add(gear);

        // Click card to open detail panel
        const hitArea = this.add.zone(AGENT_CARD_W / 2, AGENT_CARD_H / 2, AGENT_CARD_W, AGENT_CARD_H)
            .setInteractive({ useHandCursor: true });
        hitArea.on('pointerdown', () => {
            if (typeof openDetail === 'function') openDetail(agent);
        });
        container.add(hitArea);

        container.setDepth(10);
        this.agentSprites[agent.id] = { container };
    }

    drawPixelCharacter(gfx, x, y, bodyColor, state) {
        const s = 4; // pixel size

        // Head (skin)
        const skinColor = 0xffdbac;
        gfx.fillStyle(skinColor, 1);
        gfx.fillRect(x + 3*s, y, 2*s, 2*s);       // head top
        gfx.fillRect(x + 2*s, y + 2*s, 4*s, 3*s);  // face

        // Eyes
        gfx.fillStyle(0x222222, 1);
        gfx.fillRect(x + 3*s, y + 3*s, s, s);      // left eye
        gfx.fillRect(x + 5*s, y + 3*s, s, s);       // right eye

        // Hair
        gfx.fillStyle(0x3d3d3d, 1);
        gfx.fillRect(x + 2*s, y, 4*s, 2*s);

        // Body
        gfx.fillStyle(bodyColor, 1);
        gfx.fillRect(x + 1*s, y + 5*s, 6*s, 4*s);  // torso

        // Arms
        gfx.fillStyle(bodyColor, 1);
        if (state === 'writing' || state === 'executing') {
            // Arms up (typing)
            gfx.fillRect(x, y + 5*s, s, 3*s);
            gfx.fillRect(x + 7*s, y + 5*s, s, 3*s);
            // Hands
            gfx.fillStyle(skinColor, 1);
            gfx.fillRect(x, y + 8*s, s, s);
            gfx.fillRect(x + 7*s, y + 8*s, s, s);
        } else {
            // Arms down
            gfx.fillRect(x, y + 5*s, s, 4*s);
            gfx.fillRect(x + 7*s, y + 5*s, s, 4*s);
            gfx.fillStyle(skinColor, 1);
            gfx.fillRect(x, y + 9*s, s, s);
            gfx.fillRect(x + 7*s, y + 9*s, s, s);
        }

        // Legs
        gfx.fillStyle(0x2e2e4a, 1);
        gfx.fillRect(x + 2*s, y + 9*s, 2*s, 3*s);
        gfx.fillRect(x + 5*s, y + 9*s, 2*s, 3*s);

        // Shoes
        gfx.fillStyle(0x444444, 1);
        gfx.fillRect(x + 1*s, y + 12*s, 3*s, s);
        gfx.fillRect(x + 5*s, y + 12*s, 3*s, s);
    }

    drawZoomControls() {
        const zoomY = CANVAS_H - 30;
        const zoomX = 40;

        // Zoom In
        const zInBg = this.add.graphics();
        zInBg.fillStyle(COLORS.panel, 0.9);
        zInBg.fillRoundedRect(zoomX - 14, zoomY - 12, 28, 24, 6);
        zInBg.lineStyle(1, COLORS.border, 0.8);
        zInBg.strokeRoundedRect(zoomX - 14, zoomY - 12, 28, 24, 6);
        const zInTxt = this.add.text(zoomX, zoomY, '+', {
            fontSize: '14px', fontFamily: "'ArkPixel', 'Courier New', monospace", color: '#fffffe',
        }).setOrigin(0.5, 0.5);
        const zInHit = this.add.zone(zoomX, zoomY, 28, 24).setInteractive({ useHandCursor: true });
        zInHit.on('pointerdown', () => this.setZoom(this.currentZoom + 0.25));

        // Zoom Out
        const zOutX = zoomX + 36;
        const zOutBg = this.add.graphics();
        zOutBg.fillStyle(COLORS.panel, 0.9);
        zOutBg.fillRoundedRect(zOutX - 14, zoomY - 12, 28, 24, 6);
        zOutBg.lineStyle(1, COLORS.border, 0.8);
        zOutBg.strokeRoundedRect(zOutX - 14, zoomY - 12, 28, 24, 6);
        const zOutTxt = this.add.text(zOutX, zoomY, '-', {
            fontSize: '14px', fontFamily: "'ArkPixel', 'Courier New', monospace", color: '#fffffe',
        }).setOrigin(0.5, 0.5);
        const zOutHit = this.add.zone(zOutX, zoomY, 28, 24).setInteractive({ useHandCursor: true });
        zOutHit.on('pointerdown', () => this.setZoom(this.currentZoom - 0.25));

        // Reset
        const zResetX = zOutX + 40;
        const zResetBg = this.add.graphics();
        zResetBg.fillStyle(COLORS.panel, 0.9);
        zResetBg.fillRoundedRect(zResetX - 18, zoomY - 12, 36, 24, 6);
        zResetBg.lineStyle(1, COLORS.border, 0.8);
        zResetBg.strokeRoundedRect(zResetX - 18, zoomY - 12, 36, 24, 6);
        const zResetTxt = this.add.text(zResetX, zoomY, '1:1', {
            fontSize: '10px', fontFamily: "'ArkPixel', 'Courier New', monospace", color: '#94a1b2',
        }).setOrigin(0.5, 0.5);
        const zResetHit = this.add.zone(zResetX, zoomY, 36, 24).setInteractive({ useHandCursor: true });
        zResetHit.on('pointerdown', () => this.setZoom(1.0));

        // Zoom label
        this.zoomLabel = this.add.text(zResetX + 34, zoomY, '100%', {
            fontSize: '9px', fontFamily: "'ArkPixel', 'Courier New', monospace", color: '#555',
        }).setOrigin(0, 0.5);
    }

    setZoom(level) {
        this.currentZoom = Math.max(0.5, Math.min(2.0, level));
        this.cameras.main.setZoom(this.currentZoom);
        if (this.zoomLabel) {
            this.zoomLabel.setText(`${Math.round(this.currentZoom * 100)}%`);
        }
    }

    promptAddAgent() {
        const id = prompt('Agent ID (英數字):');
        if (!id) return;
        const name = prompt('Agent Name:');
        if (!name) return;

        fetch('/agents', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id.trim(), name: name.trim() }),
        }).then(res => {
            if (res.ok) this.fetchAgents();
            else res.json().then(d => alert(d.error || 'Failed'));
        }).catch(e => alert('Error: ' + e.message));
    }
}

// --- Launch Phaser ---
const config = {
    type: Phaser.AUTO,
    width: CANVAS_W,
    height: CANVAS_H,
    parent: 'game-container',
    backgroundColor: '#0f0e17',
    scene: [OfficeScene],
    pixelArt: true,
    roundPixels: true,
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
    },
};

const game = new Phaser.Game(config);
