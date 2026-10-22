<x-filament-widgets::widget>
    <x-filament::section>
        <x-slot name="heading">
            <div class="flex items-center gap-2">
                <x-heroicon-o-banknotes class="h-5 w-5 text-primary-500"/>
                <span>Кредитные предложения</span>
            </div>
        </x-slot>

        <x-slot name="description">
            Подборка актуальных предложений от Альфа-Банка
        </x-slot>

        <div class="grid auto-rows-fr grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
            @foreach ($offers as $offer)
                <div @class([
                    'group relative flex h-full flex-col overflow-hidden rounded-2xl border p-5 transition-all duration-300',
                    'border-gray-200 bg-white hover:-translate-y-1 hover:border-primary-300 hover:shadow-xl',
                    'dark:border-white/10 dark:bg-gray-900 dark:hover:border-primary-500/40',])>
                    <div
                            class="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary-500 via-warning-400 to-success-500"></div>

                    <div class="flex items-start justify-between gap-3">
                        <div class="flex min-w-0 items-start gap-3">
                            <div
                                    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary-600 dark:bg-primary-500/10 dark:text-primary-400">
                                @svg($offer['icon'], 'h-5 w-5')
                            </div>
                            <div class="min-w-0">
                                <h3 class="line-clamp-2 min-h-[2.5rem] text-sm font-semibold leading-snug text-gray-950 dark:text-white">
                                    {{ $offer['title'] }}
                                </h3>
                                <p class="mt-0.5 truncate text-xs font-medium text-gray-500 dark:text-gray-400">
                                    {{ $offer['bank'] }}
                                </p>
                            </div>
                        </div>

                        <div class="flex h-6 shrink-0 items-center">
                            @if ($offer['badge'])
                                <x-filament::badge :color="$offer['badge_color']" size="sm">
                                    {{ $offer['badge'] }}
                                </x-filament::badge>
                            @endif
                        </div>
                    </div>
                    <p class="mt-3 line-clamp-2 min-h-[2rem] text-xs leading-relaxed text-gray-500 dark:text-gray-400">
                        {{ $offer['description'] }}
                    </p>
                    <div class="mt-auto pt-4">
                        <dl class="grid h-[68px] grid-cols-3 items-center gap-2 rounded-xl bg-gray-50 p-3 dark:bg-white/5">
                            <div class="flex h-full flex-col justify-center text-center">
                                <dt class="text-[10px] uppercase tracking-wide text-gray-500 dark:text-gray-400">
                                    Ставка
                                </dt>
                                <dd class="mt-0.5 text-sm font-bold text-gray-950 dark:text-white">
                                    @if ($offer['rate'] > 0)
                                        от {{ number_format($offer['rate'], 1, ',', ' ') }}%
                                    @else
                                        0%
                                    @endif
                                </dd>
                            </div>
                            <div
                                    class="flex h-full flex-col justify-center border-x border-gray-200 text-center dark:border-white/10">
                                <dt class="text-[10px] uppercase tracking-wide text-gray-500 dark:text-gray-400">Сумма
                                </dt>
                                <dd class="mt-0.5 text-sm font-bold text-gray-950 dark:text-white">
                                    до {{ number_format($offer['amount'] / 1_000_000, 1, ',', ' ') }} млн ₽
                                </dd>
                            </div>
                            <div class="flex h-full flex-col justify-center text-center">
                                <dt class="text-[10px] uppercase tracking-wide text-gray-500 dark:text-gray-400">Срок
                                </dt>
                                <dd class="mt-0.5 text-sm font-bold text-gray-950 dark:text-white">
                                    @if ($offer['term'])
                                        до {{ $offer['term'] }} мес.
                                    @else
                                        —
                                    @endif
                                </dd>
                            </div>
                        </dl>

                        <div class="mt-3">
                            <x-filament::button tag="a"
                                                href="{{App\Filament\Resources\Requests\Pages\CreateRequest::getUrl()}}"
                                                color="primary"
                                                size="sm"
                                                class="h-9 w-full"
                                                icon="heroicon-m-arrow-right"
                                                icon-position="after">
                                Подать заявку
                            </x-filament::button>
                        </div>
                    </div>
                </div>
            @endforeach
        </div>
    </x-filament::section>
</x-filament-widgets::widget>
