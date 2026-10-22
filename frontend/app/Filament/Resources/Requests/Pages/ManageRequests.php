<?php

namespace App\Filament\Resources\Requests\Pages;

use App\Filament\Resources\Requests\RequestResource;
use App\Models\Request;
use Filament\Actions\Action;
use Filament\Actions\DeleteAction;
use Filament\Actions\ViewAction;
use Filament\Forms\Components\TextInput;
use Filament\Infolists\Components\TextEntry;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\EditRecord;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;

class ManageRequests extends EditRecord
{
    protected static string $resource = RequestResource::class;

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextEntry::make('id')
                    ->label('ID заявки')
            ])
            ->statePath('data') // Все данные формы будут храниться в свойстве $data
            ->record($this->getRecord()); // Привязка формы к текущей записи
    }

    protected function getFormActions(): array
    {
        return array_merge([
            Action::make('accept')
                ->label('Принять заявку')
                ->color('success')
                ->requiresConfirmation()
                ->modalIcon('heroicon-o-exclamation-circle')
                ->modalHeading('Одобрить заявку') // Заголовок
                ->modalDescription('Вы уверены, что хотите одобрить эту заявку?')
                ->modalSubmitActionLabel('Да, одобрить') // Текст кнопки подтверждения
//                ->modalIconColor('danger')
                ->action(function ($record) {
                    $record->status = Request::REQUEST_ACCEPTED;
                    $record->save();
                    //dd('Одобрено!');
                }),
            Action::make('reject')
                ->label('Отклонить заявку')
                ->color('danger')
                ->requiresConfirmation()
                ->modalIcon('heroicon-o-exclamation-circle')
                ->modalHeading('Отклонить заявку') // Заголовок
                ->modalDescription('Вы уверены, что хотите отклонить эту заявку?')
                ->modalSubmitActionLabel('Да, отклонить') // Текст кнопки подтверждения
                ->modalIconColor('danger')
                ->action(function ($record) {
                    $record->status = Request::REQUEST_REJECTED;
                    $record->save();
                    //dd('Отклонено!');
                }),
//            $this->getSaveFormAction()
//                ->label('Применить'),
//            $this->getCancelFormAction()
//                ->label('Назад')
//                ->url($this->getResource()::getUrl('index')),
        ]);
    }

    protected function getHeaderActions(): array
    {

        return [
            ViewAction::make(),
            DeleteAction::make(),
        ];
    }
}
