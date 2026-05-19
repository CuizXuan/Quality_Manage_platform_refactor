# CyberConfirm Component Specification

## 1. Concept & Vision

A popover-style confirmation bubble for dangerous actions in the Quality Manage platform. Replaces `ElMessageBox.confirm` with a sleek, inline confirmation that keeps the user in context. The cyber aesthetic reinforces the platform's high-tech identity — neon borders, dark glass backgrounds, and surgical precision in micro-interactions.

## 2. Design Language

### Aesthetic Direction
Cyber-industrial: dark void backgrounds with neon accent lighting. Every border glows faintly like a circuit trace. Danger operations shift the palette to hot pink.

### Color Palette
| Token | Hex | Usage |
|-------|-----|-------|
| `--neon-cyan` | `#0ff` | Primary border/glow |
| `--neon-pink` | `#ff00aa` | Danger action button |
| `--bg-panel` | `#0d0d14` | Popover background |
| `--text-primary` | `#e0e0e0` | Body text |
| `--text-secondary` | `#888` | Subdued text |

### Typography
- **Title**: Orbitron 600, 12px, letter-spacing 2px
- **Body**: Fira Code 400, 12px
- **Buttons**: Fira Code 500, 11px

### Spatial System
- Popover padding: 16px
- Border-radius: 8px
- Button gap: 8px
- Icon size: 16px
- Popover min-width: 200px

### Motion Philosophy
- **Enter**: opacity 0→1 + scale 0.95→1, 200ms ease-out
- **Leave**: opacity 1→0, 150ms ease-in
- Purpose: snappy confirmation that feels responsive but not jarring

### Visual Assets
- Warning icon: inline SVG triangle-exclamation
- Button icons: inline SVG checkmark (confirm) and X (cancel)
- No emoji in component internals

## 3. Layout & Structure

```
[Trigger Slot] → click → [Popover Bubble]
                                 ┌─────────────────────────┐
                                 │ ⚠  Confirm delete?      │
                                 │  [Cancel]  [Delete]     │
                                 └─────────────────────────┘
```

- Trigger: arbitrary content (usually a button), positioned `relative`
- Popover: `position: absolute`, appears below-right of trigger by default
- Popover has a 1px neon cyan border with subtle box-shadow glow
- Click outside popover → close
- ESC key → close

## 4. Features & Interactions

### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | String | `'确认操作？'` | Bubble title text |
| `okText` | String | `'确认'` | Confirm button label |
| `cancelText` | String | `'取消'` | Cancel button label |
| `danger` | Boolean | `false` | If true, confirm button is pink/danger styled |

### Slots
| Slot | Description |
|------|-------------|
| `default` / `trigger` | The element that triggers the popover |

### Events
| Event | Payload | Description |
|-------|---------|-------------|
| `confirm` | — | User clicked confirm |
| `cancel` | — | User clicked cancel or clicked outside |

### Behavior
- **Show**: Click trigger → popover appears with animation
- **Hide (cancel)**: Click cancel button OR click outside popover OR press ESC
- **Confirm**: Click confirm → emit `confirm`, close popover
- **Close on outside click**: Listen for mousedown on document (not click, to avoid bubbling issues)

## 5. Component Inventory

### CyberConfirm.vue
- **Default state**: Popover hidden
- **Open state**: Popover visible with fade+scale animation
- **Danger variant**: Confirm button has pink border/text instead of cyan

### Usage in CaseManagement.vue
```vue
<CyberConfirm
  title="确认删除这个用例？"
  ok-text="删除"
  cancel-text="取消"
  danger
  @confirm="caseStore.deleteCase(id)"
>
  <template #trigger>
    <button class="icon-btn danger" title="删除">🗑</button>
  </template>
</CyberConfirm>
```

## 6. Technical Approach

- **Framework**: Vue 3 Composition API (`<script setup>`)
- **No external UI library**: Pure Vue + CSS (no Element Plus Popconfirm dependency)
- **Positioning**: CSS `position: absolute` relative to trigger wrapper
- **Teleport**: Use `<Teleport to="body">` for proper z-index stacking
- **Click outside**: `mousedown` event listener on `document` with flag to avoid self-click
- **ESC key**: `keydown` listener on `document`
- **Global registration**: In `main.ts`, import and `app.component('CyberConfirm', CyberConfirm)`
