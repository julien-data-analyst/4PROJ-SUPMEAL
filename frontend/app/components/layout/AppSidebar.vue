<script setup lang="ts">
import AppLogo from "~/components/AppLogo.vue";
import IconHome from "~/components/icons/IconHome.vue";
import IconRecipe from "~/components/icons/IconRecipe.vue";
import IconCookbook from "~/components/icons/IconCookbook.vue";
import IconShared from "~/components/icons/IconShared.vue";
import IconCalendar from "~/components/icons/IconCalendar.vue";
import IconSearch from "~/components/icons/IconSearch.vue";
import IconImportExport from "~/components/icons/IconImportExport.vue";
import IconSettings from "~/components/icons/IconSettings.vue";
import IconLogout from "~/components/icons/IconLogout.vue";
import { useAuth } from "~/composables/useAuth";

const route = useRoute();
const { user } = useAuth();

const navItems = [
  { to: "/home", label: "Accueil", icon: IconHome },
  { to: "/recipes", label: "Mes recettes", icon: IconRecipe },
  { to: "/cookbooks", label: "Cookbooks", icon: IconCookbook },
  { to: "/sharedwithme", label: "Partagés avec moi", icon: IconShared },
  { to: "/planning", label: "Planning repas", icon: IconCalendar },
  { to: "/search", label: "Recherche", icon: IconSearch },
  { to: "/import_export", label: "Importer / Exporter", icon: IconImportExport },
];

const navItemClasses =
  "flex items-center gap-[10px] rounded-md px-[10px] py-[9px] text-[14px] font-medium transition-colors";

const isActive = (to: string) =>
  route.path === to || route.path.startsWith(`${to}/`);
</script>

<template>
  <aside
    class="sticky top-0 flex h-screen w-[236px] shrink-0 flex-col border-r border-sup-border bg-sup-withe px-[14px] py-5"
  >
    <div class="px-[10px] pb-[22px] pt-1">
      <AppLogo size="sm" />
    </div>

    <nav class="flex flex-1 flex-col gap-0.5 overflow-y-auto">
      <NuxtLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          navItemClasses,
          isActive(item.to)
            ? 'bg-sup-light-green/15 font-semibold text-sup-dark-green'
            : 'text-sup-very-gray hover:bg-sup-light-gray',
        ]"
      >
        <component :is="item.icon" size="xs" />
        {{ item.label }}
      </NuxtLink>
    </nav>

    <div class="flex flex-col gap-0.5">
      <div class="mx-1 my-[10px] h-px bg-sup-border" />

      <p v-if="user" class="truncate px-[10px] pb-1 text-[12px] text-gray-400">
        {{ user.first_name || user.username }}
      </p>

      <NuxtLink
        to="/settings"
        :class="[
          navItemClasses,
          isActive('/settings')
            ? 'bg-sup-light-green/15 font-semibold text-sup-dark-green'
            : 'text-sup-very-gray hover:bg-sup-light-gray',
        ]"
      >
        <IconSettings size="xs" />
        Paramètres
      </NuxtLink>

      <div class="mx-1 my-[10px] h-px bg-sup-border" />

      <NuxtLink :class="[navItemClasses, 'text-sup-red-error hover:bg-sup-red-error/10']" to="/logout">
        <IconLogout size="xs" />
        Déconnexion
      </NuxtLink>
    </div>
  </aside>
</template>
