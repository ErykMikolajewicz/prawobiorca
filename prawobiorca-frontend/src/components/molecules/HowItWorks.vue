<script setup lang="ts">
import DescriptionOutlineRoundedIcon from '@iconify-vue/material-symbols/description-outline-rounded'
import ChatOutlineRoundedIcon from '@iconify-vue/material-symbols/chat-outline-rounded'
import GavelRoundedIcon from '@iconify-vue/material-symbols/gavel-rounded'
import ChevronRightRoundedIcon from '@iconify-vue/material-symbols/chevron-right-rounded'

import FeatureItem from '@/components/molecules/FeatureItem.vue'

const steps = [
  {
    icon: DescriptionOutlineRoundedIcon,
    title: 'Wybierz akt prawny',
    description: 'Kliknij regulację z listy poniżej.',
  },
  {
    icon: ChatOutlineRoundedIcon,
    title: 'Zadaj pytanie',
    description: 'Napisz, czego chciałbyś się dowiedzieć.',
  },
  {
    icon: GavelRoundedIcon,
    title: 'Poznaj przepisy',
    description: 'Zobacz artykuły, które najlepiej pasują do pytania.',
  },
]
</script>

<template>
  <section class="how-it-works">
    <h2 class="how-it-works-title">Jak to działa?</h2>

    <ol class="steps app-list-reset">
      <template v-for="(step, index) in steps" :key="step.title">
        <li class="step">
          <FeatureItem
            :icon="step.icon"
            :title="`${index + 1}. ${step.title}`"
            :description="step.description"
          />
        </li>
        <ChevronRightRoundedIcon v-if="index < steps.length - 1" class="step-separator" />
      </template>
    </ol>
  </section>
</template>

<style scoped>
.how-it-works {
  padding: var(--app-space-xl);
  margin-bottom: var(--app-space-xl);
  border: 1px solid var(--el-color-primary-light-7);
  border-radius: var(--app-radius-lg);
  background: linear-gradient(135deg, var(--el-color-primary-light-9), var(--app-card-bg));
}

.how-it-works-title {
  margin: 0 0 var(--app-space-lg);
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.steps {
  display: flex;
  align-items: center;
  gap: var(--app-space-lg);
}

.step {
  flex: 1;
}

.step-separator {
  flex-shrink: 0;
  width: 1em;
  height: 1em;
  font-size: 1.5rem;
  color: var(--el-color-primary-light-5);
}

@media (width <= 768px) {
  .steps {
    flex-direction: column;
    align-items: stretch;
  }

  .step-separator {
    display: none;
  }
}
</style>
