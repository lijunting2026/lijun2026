# Add global transitions to App.vue
with open('../frontend/src/App.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# Add page transition
if 'fade-slide' not in content:
    content = content.replace(
        '<router-view />',
        '<router-view v-slot=\"{ Component }\">\n    <transition name=\"fade-slide\" mode=\"out-in\">\n      <component :is=\"Component\" />\n    </transition>\n  </router-view>'
    )
    
    # Add transition styles
    style_add = '''
/* Page transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* Global skeleton animation */
@keyframes shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}
.skeleton {
  background: linear-gradient(90deg, #f0f2f5 25%, #e8eaed 37%, #f0f2f5 63%);
  background-size: 200px 100%;
  animation: shimmer 1.4s ease infinite;
  border-radius: 4px;
}

/* Card hover effect */
.el-card {
  transition: box-shadow 0.3s ease, transform 0.2s ease;
}
.el-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* Responsive table */
@media (max-width: 768px) {
  .el-table .cell {
    white-space: normal !important;
  }
}
'''
    # Insert styles before </style>
    content = content.replace('</style>', style_add + '\n</style>')

with open('../frontend/src/App.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print('App.vue updated with transitions')
