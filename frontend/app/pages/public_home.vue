<script setup lang="ts">
import AppLogo from "~/components/AppLogo.vue";
import AppButton from "~/components/buttons/AppButton.vue";
import IconRecipe from "~/components/icons/IconRecipe.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import IconCalendar from "~/components/icons/IconCalendar.vue";

definePageMeta({ layout: false });

const features = [
  {
    title: "Recettes",
    description:
      "Rédigez, éditez et organisez toutes vos recettes au même endroit.",
    icon: markRaw(IconRecipe),
  },
  {
    title: "Cookbooks",
    description:
      "Regroupez vos recettes par thème et partagez-les avec vos proches.",
    icon: markRaw(IconCookbook),
  },
  {
    title: "Planning repas",
    description:
      "Planifiez vos repas de la semaine et générez vos listes de courses.",
    icon: markRaw(IconCalendar),
  },
];
</script>

<template>
  <div
    class="flex min-h-screen flex-col bg-gradient-to-br from-sup-light-green/10 via-sup-light-gray to-sup-light-gray"
  >
    <header
      class="flex items-center justify-between px-6 py-6 sm:px-10 lg:px-16"
    >
      <AppLogo size="sm" />
      <div class="flex items-center gap-3">
        <AppButton to="/login" variant="ghost">Se connecter</AppButton>
        <AppButton to="/register" variant="primary">Créer un compte</AppButton>
      </div>
    </header>

    <main
      class="flex flex-1 items-center justify-center px-6 py-16 sm:px-10 lg:px-16"
    >
      <div class="w-full max-w-5xl text-center">
        <AppLogo size="lg" />

        <h1
          class="mx-auto mt-10 max-w-4xl text-4xl font-extrabold leading-tight text-sup-very-gray sm:text-5xl lg:text-6xl"
        >
          Vos recettes, cookbooks
          <span class="block">&amp; plannings, au même endroit.</span>
        </h1>

        <p class="mx-auto mt-6 max-w-2xl text-lg text-gray-500 sm:text-xl">
          SUPMEAL centralise vos recettes, vos cookbooks et vos plannings de
          repas pour une organisation culinaire simple, sans effort et
          accessible partout.
        </p>

        <div
          class="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
        >
          <AppButton
            to="/register"
            variant="primary"
            size="lg"
            class="w-full sm:w-auto"
          >
            Créer un compte gratuitement
          </AppButton>
          <AppButton
            to="/login"
            variant="secondary"
            size="lg"
            class="w-full sm:w-auto"
          >
            Se connecter
          </AppButton>
        </div>
      </div>
    </main>

    <section class="px-6 pb-20 sm:px-10 lg:px-16">
      <div class="mx-auto grid max-w-5xl gap-6 sm:grid-cols-3">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="rounded-2xl border border-sup-border bg-sup-withe p-7 text-center shadow-sm"
        >
          <div
            class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sup-light-green/15 text-sup-dark-green"
          >
            <component :is="feature.icon" size="lg" />
          </div>
          <h2 class="mt-5 text-lg font-bold text-sup-very-gray sm:text-xl">
            {{ feature.title }}
          </h2>
          <p class="mt-2 text-sm text-gray-500 sm:text-base">
            {{ feature.description }}
          </p>
        </div>
      </div>
    </section>
  </div>
</template>
